import asyncio
import logging
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .history import HistoryManager
from .gemini import GroqClient
from .evolution import EvolutionClient
from .chatwoot import ChatwootClient

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
    logger.info("🚀 Starting up — loading conversation history from Chatwoot...")
    try:
        await history_manager.load_from_chatwoot(chatwoot_client)
        logger.info("✅ History loaded successfully.")
    except Exception as e:
        logger.warning(f"⚠️  Could not load history on startup: {e}")
    yield
    logger.info("🛑 Shutting down.")


app = FastAPI(
    title="Chatwoot → Gemini → Evolution API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook/chatwoot/conversa")
async def chatwoot_webhook(request: Request):
    print(f"Received webhook: {await request.body()}")

@app.post("/webhook/chatwoot")
async def chatwoot_webhook(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    event = body.get("event")
    logger.info(f"📨 Webhook received: event={event}")

    if event not in ("message_created", "message_updated"):
        return {"status": "ignored", "reason": f"event '{event}' not handled"}

    message_type = body.get("message_type", "")
    if message_type != "incoming":
        return {"status": "ignored", "reason": f"message_type '{message_type}' — skipped"}

    if body.get("private", False):
        return {"status": "ignored", "reason": "private message — skipped"}

    content = (body.get("content") or "").strip()
    if not content:
        return {"status": "ignored", "reason": "empty content"}

    conversation_id = str(body.get("conversation", {}).get("id", ""))
    message_id = str(body.get("id", ""))

    # sender info
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