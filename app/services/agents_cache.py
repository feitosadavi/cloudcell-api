import os
import re
import logging

from app.database import listar_admins

logger = logging.getLogger(__name__)


def normalize(phone: str) -> str:
    return re.sub(r"\D", "", phone or "")


class AgentsCache:

    def __init__(self):

        self.admin_phones = set()

    async def load(self):

        self.admin_phones.clear()

        # 1️⃣ admins do ENV
        env_admins = os.getenv("ADMIN_PHONES", "")

        if env_admins:
            for p in env_admins.split(","):
                self.admin_phones.add(normalize(p))

        # 2️⃣ admins do banco
        for p in listar_admins():
            self.admin_phones.add(normalize(p))

        logger.info(f"🔐 Admin phones carregados: {self.admin_phones}")

    def add_admin(self, phone: str):

        from app.database import adicionar_admin

        phone = normalize(phone)

        adicionar_admin(phone)

        self.admin_phones.add(phone)

    def remove_admin(self, phone: str):

        from app.database import remover_admin

        phone = normalize(phone)

        remover_admin(phone)

        self.admin_phones.discard(phone)

    def is_admin(self, phone: str) -> bool:

        phone = normalize(phone)
        print(f"Verificando admin: {phone} in {self.admin_phones}")
        return phone in self.admin_phones


agents_cache = AgentsCache()