# app/main.py
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .history import HistoryManager
from .gemini import GroqClient
from .evolution import EvolutionClient
from .chatwoot import ChatwootClient
from .proccess_commands import proccess_commands
from .admin_routes import router as admin_router
from app.services.agents_cache import agents_cache
from app.services.agents_cache import agents_cache
from app.services.bot_service import bot_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

history_manager = HistoryManager()
gemini_client = GroqClient()
evolution_client = EvolutionClient()
chatwoot_client = ChatwootClient()

# ---------------------------------------------------------------------
# Config / estado global
# ---------------------------------------------------------------------
# Prefixos que serão tratados como comandos. Ajuste conforme desejar.
# Para aceitar qualquer comando que comece com `/` use: COMMAND_PREFIXES = ("/",)
COMMAND_PREFIXES = ("/",)

# dedupe simples em memória (troque por Redis para multi-instance)
_seen_messages: set[str] = set()

# ---------------------------------------------------------------------
# Lifespan: inicialização (DB, histórico, cache de agentes)
# ---------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🗄️ Inicializando banco...")
    init_db()

    logger.info("🚀 Carregando histórico...")
    try:
        await history_manager.load_from_chatwoot(chatwoot_client)
    except Exception as e:
        logger.warning(f"⚠️ Falha ao carregar histórico: {e}")

    logger.info("👤 Carregando agentes Chatwoot (cache)...")
    try:
        await agents_cache.load()
    except Exception as e:
        logger.warning(f"⚠️ Falha ao carregar agents cache: {e}")

    try:
        await bot_service.load()
    except Exception as e:
        logger.warning(f"⚠️ Falha ao carregar bots cache: {e}")


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


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------
# Único endpoint de webhook (unifica comando e mensagem normal)
# ---------------------------------------------------------------------
@app.post("/webhook/chatwoot")
async def chatwoot_webhook(request: Request, background: BackgroundTasks):
    """
    Recebe eventos do Chatwoot:
      - message_created (incoming)
      - message_updated
      - agent_updated (atualiza cache)
    """

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    event = body.get("event")
    logger.info(f"📨 Webhook recebido: event={event}")

    # Tratamos exclusivamente esses eventos
    if event not in ("message_created", "message_updated", "agent_updated"):
        return {"status": "ignored", "reason": f"event '{event}' não tratado"}

    # ---------------------------
    # Atualização de agente
    # ---------------------------
    if event == "agent_updated":
        agent = body.get("agent")
        if agent:
            try:
                agents_cache.update_agent(agent)
            except Exception as e:
                logger.exception("Erro ao atualizar agent cache")
        return {"status": "ok"}

    # ---------------------------
    # Mensagens (created / updated)
    # ---------------------------
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
    sender = body.get("sender", {}) or {}

    # dedupe
    if message_id in _seen_messages:
        logger.info(f"⚠️ Mensagem duplicada: {message_id}")
        return {"status": "ignored", "reason": "duplicate"}
    _seen_messages.add(message_id)

    # ---------------------------
    # Mensagem normal → pipeline AI + Evolution
    # ---------------------------
    # phone number from Chatwoot conversation meta
    phone_number = (
        body.get("conversation", {})
        .get("meta", {})
        .get("sender", {})
        .get("phone_number", "")
    )

    # Detecta se é comando
    lower = content.lower()
    is_command = any(lower.startswith(pref) for pref in COMMAND_PREFIXES) or (content.startswith("/") and content.split()[0] in [p.lstrip("/") for p in COMMAND_PREFIXES])
    if is_command:
        try:
            # agents_cache.is_admin é async (faz refresh TTL) — await
            allowed = agents_cache.is_admin(phone_number)
        except Exception as e:
            logger.exception("Erro verificando admin no cache")
            # política: negar por segurança se check falhar
            allowed = False

        if not allowed:
            logger.info("⛔ Comando ignorado: não é admin (phone=%s)", phone_number)
            return {"status": "ignored", "reason": "not admin"}
        
        # delega ao service de comandos (processar_webhook) em background
        background.add_task(proccess_commands, content, phone_number, evolution_client)

        logger.info("🛠️ Comando detectado e autorizado (phone_number=%s): %s", phone_number, content[:120])

        return {"status": "ok", "type": "command"}

    if not conversation_id or not phone_number:
        raise HTTPException(status_code=422, detail="Missing conversation_id or phone_number")

    # Remove "+"
    phone_number = phone_number.replace("+", "")

    logger.info(
        f"💬 New message | conv={conversation_id} phone={phone_number} ({sender.get('name')}) | {content[:80]}"
    )

    # Processa mensagem normal (em background)
    async def _handle_normal():
        history_manager.add_message(conversation_id, message_id, role="user", content=content)
        history = history_manager.get_history(conversation_id)

        try:
            reply = await gemini_client.chat(history)
        except Exception as e:
            logger.error(f"❌ Gemini error: {e}")
            return

        logger.info(f"🤖 Gemini reply: {reply[:120]}")

        history_manager.add_message(
            conversation_id,
            f"assistant-{message_id}",
            role="assistant",
            content=reply
        )

        try:
            await evolution_client.send_message(number=phone_number, message=reply)
        except Exception as e:
            logger.error(f"❌ Evolution API error: {e}")

    background.add_task(_handle_normal)

    return {"status": "ok", "type": "normal"}