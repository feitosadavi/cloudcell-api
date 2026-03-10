import logging
import httpx

from .config import settings

logger = logging.getLogger(__name__)


class EvolutionClient:
    """
    Sends messages to the Evolution API.
    POST {EVOLUTION_URL}/messages
    Authorization: Bearer AUTHENTICATION_API_KEY
    """

    def __init__(self):
        self._client = httpx.AsyncClient(
            base_url=settings.evolution_url.rstrip("/"),
            headers={
                "apikey": settings.evolution_api_key,
                "Content-Type": "application/json",
            },
            timeout=settings.request_timeout,
        )

    async def send_message(self, number: str, message: str) -> dict:
        payload = {
            "number": number,
            "text": message,
        }

        logger.info(f"📤 Evolution | number={number}")

        response = await self._client.post(
            f"/message/sendText/{settings.evolution_instance}",
            json=payload
        )

        response.raise_for_status()
        return response.json()

    async def aclose(self):
        await self._client.aclose()
