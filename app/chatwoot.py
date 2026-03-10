import logging
import httpx

from .config import settings

logger = logging.getLogger(__name__)


class ChatwootClient:
    """
    Fetches conversation + message history from the Chatwoot REST API.
    GET {CHATWOOT_URL}/api/v1/accounts/{account_id}/conversations
    """

    def __init__(self):
        headers = {"Content-Type": "application/json"}
        if settings.chatwoot_api_token:
            headers["api_access_token"] = settings.chatwoot_api_token

        self._client = httpx.AsyncClient(
            base_url=settings.chatwoot_url.rstrip("/"),
            headers=headers,
            timeout=settings.request_timeout,
            verify=False,  # self-signed cert support (sslip.io setups)
        )

    async def fetch_conversations(self) -> list[dict]:
        """
        Fetches all pages of conversations and returns a flat list.
        Each item contains 'id' and 'messages' as returned by Chatwoot.
        """
        account_id = settings.chatwoot_account_id
        base_path = f"/api/v1/accounts/{account_id}/conversations"

        all_conversations = []
        page = 1

        while True:
            logger.info(f"🔄 Fetching Chatwoot conversations page {page}...")
            try:
                response = await self._client.get(base_path, params={"page": page})
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                logger.warning(f"Chatwoot HTTP error on page {page}: {e}")
                break
            except Exception as e:
                logger.warning(f"Chatwoot fetch error: {e}")
                break

            # Response shape: { data: { payload: [...], meta: {...} } }
            payload = (
                data.get("data", {}).get("payload")
                or data.get("payload")
                or []
            )

            if not payload:
                break

            for conv in payload:
                conv_id = conv.get("id")
                messages = conv.get("messages", [])

                # Extract only what we need: id, content, message_type, sender
                slim_messages = []
                for m in messages:
                    slim_messages.append({
                        "id": m.get("id"),
                        "content": m.get("content"),
                        "message_type": m.get("message_type", 0),
                        "created_at": m.get("created_at", 0),
                        "sender": m.get("sender", {}),
                    })

                all_conversations.append({
                    "id": conv_id,
                    "messages": slim_messages,
                    # Useful metadata
                    "contact_id": conv.get("meta", {}).get("sender", {}).get("id"),
                    "contact_name": conv.get("meta", {}).get("sender", {}).get("name"),
                })

            meta = data.get("data", {}).get("meta", {})
            all_count = meta.get("all_count", 0)
            fetched = page * len(payload)
            if fetched >= all_count or len(payload) == 0:
                break
            page += 1

        logger.info(f"📋 Fetched {len(all_conversations)} conversations from Chatwoot")
        return all_conversations

    async def aclose(self):
        await self._client.aclose()
