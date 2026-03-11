"""
LangChain Tools:
  - consultar_estoque        busca fuzzy no SQLite
  - listar_estoque_completo  lista tudo disponível
  - transbordo               transfere para atendimento humano via Chatwoot
"""
import asyncio
import logging
from collections import Counter

import httpx
from langchain_core.tools import tool

from .config import settings
from .database import buscar_produtos, formatar_produto, listar_produtos

logger = logging.getLogger(__name__)

# conversation_id injetado pelo gemini.py antes de cada chat()
_current_conversation_id: str = ""


def set_conversation_id(cid: str):
    global _current_conversation_id
    _current_conversation_id = cid


# ── Helpers Chatwoot ──────────────────────────────────────────────────────────

async def _executar_transbordo(conversation_id: str, motivo: str) -> str:
    base     = settings.chatwoot_url.rstrip("/")
    account  = settings.chatwoot_account_id
    headers  = {"api_access_token": settings.chatwoot_api_token}

    async with httpx.AsyncClient(timeout=15, verify=False) as client:

        # 1. Busca agentes
        r = await client.get(
            f"{base}/api/v1/accounts/{account}/agents",
            headers=headers,
        )
        r.raise_for_status()
        agentes = r.json()
        def _nao_e_admin(a: dict) -> bool:
            nome = (a.get("name") or "").strip().lower()
            email = (a.get("email") or "").strip().lower()
            return nome != "admin" and not email.startswith("admin@")

        disponiveis = [a for a in agentes if a.get("availability_status") in ("online", "busy") and _nao_e_admin(a)]
        if not disponiveis:
            disponiveis = [a for a in agentes if _nao_e_admin(a)]   # fallback: usa todos menos admin
        if not disponiveis:
            return "Atendente"

        # 2. Conta conversas abertas por agente
        r = await client.get(
            f"{base}/api/v1/accounts/{account}/conversations"
            f"?assignee_type=assigned&status=open&page=1",
            headers=headers,
        )
        r.raise_for_status()
        payload = r.json().get("data", {}).get("payload", [])
        contador = Counter()
        for conv in payload:
            assignee = conv.get("meta", {}).get("assignee")
            if assignee:
                contador[assignee["id"]] += 1

        # 3. Agente com menor carga
        agente      = min(disponiveis, key=lambda a: contador.get(a["id"], 0))
        agente_id   = agente["id"]
        agente_nome = agente.get("name", "Atendente")
        logger.info(f"🎯 Transbordo → {agente_nome} (id={agente_id}, conv={conversation_id})")

        # 4. Atribui a conversa
        await client.post(
            f"{base}/api/v1/accounts/{account}/conversations/{conversation_id}/assignments",
            headers={**headers, "Content-Type": "application/json"},
            json={"assignee_id": agente_id},
        )

        return agente_nome


# ── Tools ─────────────────────────────────────────────────────────────────────

@tool
def consultar_estoque(query: str) -> str:
    """
    Busca produtos no estoque por nome, modelo, cor, armazenamento ou tipo.
    Use esta ferramenta SEMPRE que o cliente perguntar sobre disponibilidade,
    preço ou especificações de qualquer produto.
    Exemplos: 'iphone 13 preto', 'samsung 128gb', 'seminovo android'.
    NUNCA invente produtos — use apenas o que esta ferramenta retornar.
    """
    logger.info(f"🔍 Consulta estoque: '{query}'")
    produtos = buscar_produtos(query, limite=50)
    logger.info(f"🔍 Resultados: {len(produtos)} para '{query}'")

    if not produtos:
        return "NENHUM_PRODUTO_ENCONTRADO"

    linhas = [f"Encontrei {len(produtos)} produto(s) disponível(is):\n"]
    for p in produtos:
        linhas.append(formatar_produto(p))
        linhas.append("")
    return "\n".join(linhas)


@tool
def listar_estoque_completo(filtro: str = "") -> str:
    """
    Lista todos os produtos disponíveis no estoque.
    Use quando o cliente pedir para ver tudo disponível.
    O parâmetro filtro é opcional: 'seminovo', 'novo', 'iphone', etc.
    """
    logger.info(f"📋 Listagem completa, filtro='{filtro}'")
    produtos = listar_produtos(apenas_disponiveis=True)

    if filtro:
        fl = filtro.lower()
        produtos = [
            p for p in produtos
            if fl in (p.get("tipo") or "").lower()
            or fl in (p.get("estado") or "").lower()
            or fl in (p.get("nome") or "").lower()
        ]

    if not produtos:
        return "Nenhum produto disponível no estoque no momento."

    linhas = [f"*Estoque disponível — {len(produtos)} produto(s):*\n"]
    for p in produtos:
        linhas.append(formatar_produto(p))
        linhas.append("")
    return "\n".join(linhas)


@tool
def transbordo(motivo: str = "") -> str:
    """
    Transfere o atendimento para um operador humano.
    Use nos seguintes casos:
    - Cliente quer vender um aparelho (após receber a ficha preenchida)
    - Cliente pede explicitamente por atendimento humano / operador / gerente
    - Você não sabe responder algo importante sobre a loja ou produto
    - Situação fora do escopo normal do atendimento
    O parâmetro motivo é opcional mas ajuda o operador a entender o contexto.
    """
    logger.info(f"🔀 TRANSBORDO acionado | motivo='{motivo}' | conv={_current_conversation_id}")

    if not settings.chatwoot_api_token or not _current_conversation_id:
        logger.warning("⚠️ Token ou conversation_id ausente — transbordo simulado")
        return "TRANSBORDO_REALIZADO|agente=Atendente"

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            future = asyncio.run_coroutine_threadsafe(
                _executar_transbordo(_current_conversation_id, motivo), loop
            )
            agente_nome = future.result(timeout=20)
        else:
            agente_nome = loop.run_until_complete(
                _executar_transbordo(_current_conversation_id, motivo)
            )
        logger.info(f"✅ Transbordo concluído → {agente_nome}")
        return f"TRANSBORDO_REALIZADO|agente={agente_nome}"

    except Exception as e:
        logger.error(f"Erro no transbordo: {e}")
        return "TRANSBORDO_REALIZADO|agente=Atendente"


STOCK_TOOLS = [consultar_estoque, listar_estoque_completo, transbordo]