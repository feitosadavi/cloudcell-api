# app/services/bot_config_service.py
import logging
from typing import Optional

from ..database import db  # seu context manager db() do arquivo database.py

logger = logging.getLogger(__name__)

class BotConfigService:
    """
    Small persistence shim for bot instructions.
    Uses the same SQLite DB your app already uses (database.db()).
    Ensures the `bot_config` table exists.
    """

    def __init__(self) -> None:
        try:
            with db() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS bot_config (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    );
                    """
                )
        except Exception as e:
            logger.exception("Erro criando tabela bot_config: %s", e)
            raise

    def get_instructions(self) -> str:
        """Return stored instructions (empty string if none)."""
        try:
            with db() as conn:
                row = conn.execute(
                    "SELECT value FROM bot_config WHERE key = 'instructions'"
                ).fetchone()
                return row["value"] if row else ""
        except Exception as e:
            logger.exception("Erro lendo instruções do DB: %s", e)
            return ""

    def set_instructions(self, text: str) -> None:
        """Insert or update instructions."""
        try:
            with db() as conn:
                conn.execute(
                    """
                    INSERT INTO bot_config (key, value)
                    VALUES ('instructions', ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (text,),
                )
        except Exception as e:
            logger.exception("Erro salvando instruções no DB: %s", e)
            raise

    def delete_instructions(self) -> None:
        """Remove instructions (rarely used)."""
        try:
            with db() as conn:
                conn.execute("DELETE FROM bot_config WHERE key = 'instructions'")
        except Exception as e:
            logger.exception("Erro removendo instruções do DB: %s", e)
            raise