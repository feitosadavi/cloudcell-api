import asyncio
import logging
from collections import defaultdict, deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .chatwoot import ChatwootClient

from .config import settings

logger = logging.getLogger(__name__)


class HistoryManager:
    """
    Thread-safe, in-memory conversation history.
    Keyed by conversation_id (string).
    Each entry: {"role": "user"|"assistant", "content": "..."}
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        # conversation_id -> deque of {"role", "content"}
        self._histories: dict[str, deque] = defaultdict(
            lambda: deque(maxlen=settings.max_history_messages)
        )

    def add_message(self, conversation_id: str, message_id: str, role: str, content: str):
        self._histories[conversation_id].append({"role": role, "content": content})
        logger.debug(f"History | conv={conversation_id} +{role} (total={len(self._histories[conversation_id])})")

    def get_history(self, conversation_id: str) -> list[dict]:
        return list(self._histories[conversation_id])

    async def load_from_chatwoot(self, chatwoot_client: "ChatwootClient"):
        """
        Fetches all conversations from Chatwoot on startup and seeds the history.
        Extracts: user id, message id, message content.
        """
        conversations = await chatwoot_client.fetch_conversations()
        total_msgs = 0

        for conv in conversations:
            conv_id = str(conv.get("id", ""))
            if not conv_id:
                continue

            messages = conv.get("messages", [])
            # Sort by created_at ascending so history is in order
            messages_sorted = sorted(messages, key=lambda m: m.get("created_at", 0))

            for msg in messages_sorted:
                msg_id = str(msg.get("id", ""))
                content = (msg.get("content") or "").strip()
                if not content:
                    continue

                # message_type: 0 = incoming (contact), 1 = outgoing (agent/bot)
                mtype = msg.get("message_type", 0)
                role = "user" if mtype == 0 else "assistant"

                self.add_message(conv_id, msg_id, role, content)
                total_msgs += 1

        logger.info(f"📚 Seeded history: {len(self._histories)} conversations, {total_msgs} messages")
