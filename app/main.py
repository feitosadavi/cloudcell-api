import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .history import HistoryManager
from .gemini import GroqClient
from .evolution import EvolutionClient
from .chatwoot import ChatwootClient
from .admin_routes import router as admin_router
# from .appsheet_routes import router as appsheet_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

history_manager = HistoryManager()
gemini_client = GroqClient()
evolution_client = EvolutionClient()
chatwoot_client = ChatwootClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Banco de dados
    logger.info("🗄️  Inicializando banco de dados...")
    init_db()

    # 2. Histórico do Chatwoot
    logger.info("🚀 Carregando histórico de conversas do Chatwoot...")
    try:
        await history_manager.load_from_chatwoot(chatwoot_client)
        logger.info("✅ Histórico carregado.")
    except Exception as e:
        logger.warning(f"⚠️  Não foi possível carregar histórico: {e}")

    yield
    logger.info("🛑 Encerrando.")


app = FastAPI(
    title="Chatwoot → Gemini → Evolution API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)
# app.include_router(appsheet_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook/chatwoot")
async def chatwoot_webhook(request: Request):
    """
    Recebe eventos do webhook do Chatwoot.
    Payload real (flat, sem wrapper 'data'):
      {
        "event": "message_created",
        "message_type": "incoming",
        "content": "Olá",
        "id": 221,
        "conversation": { "id": 6, ... },
        "sender": { "id": 11, "name": "Teste", ... }
      }
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    event = body.get("event")
    logger.info(f"📨 Webhook recebido: event={event}")

    if event not in ("message_created", "message_updated"):
        return {"status": "ignored", "reason": f"event '{event}' não tratado"}

    message_type = body.get("message_type", "")
    if message_type != "incoming":
        return {"status": "ignored", "reason": f"message_type '{message_type}' ignorado"}

    if body.get("private", False):
        return {"status": "ignored", "reason": "mensagem privada ignorada"}

    content = (body.get("content") or "").strip()
    if not content:
        return {"status": "ignored", "reason": "conteúdo vazio"}

    conversation_id = str(body.get("conversation", {}).get("id", ""))
    message_id = str(body.get("id", ""))
    sender = body.get("sender", {})


    # 📞 phone number from Chatwoot metadata
    phone_number = (
        body.get("conversation", {})
        .get("meta", {})
        .get("sender", {})
        .get("phone_number", "")
    )

    if not conversation_id or not phone_number:
        raise HTTPException(status_code=422, detail="Missing conversation_id or phone_number")

    # Remove "+"
    phone_number = phone_number.replace("+", "")

    logger.info(
        f"💬 New message | conv={conversation_id} phone={phone_number} ({sender.get('name')}) | {content[:80]}"
    )

    history_manager.add_message(conversation_id, message_id, role="user", content=content)
    history = history_manager.get_history(conversation_id)

    try:
        reply = await gemini_client.chat(history)
    except Exception as e:
        logger.error(f"❌ Gemini error: {e}")
        raise HTTPException(status_code=502, detail=f"Gemini error: {e}")

    logger.info(f"🤖 Gemini reply: {reply[:120]}")

    history_manager.add_message(
        conversation_id,
        f"assistant-{message_id}",
        role="assistant",
        content=reply
    )

    try:
        await evolution_client.send_message(
            number=phone_number,
            message=reply
        )
    except Exception as e:
        logger.error(f"❌ Evolution API error: {e}")
        raise HTTPException(status_code=502, detail=f"Evolution API error: {e}")

    return {"status": "ok", "reply": reply}