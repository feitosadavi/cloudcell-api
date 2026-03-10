"""
LangChain Tools:
  - consultar_estoque        busca fuzzy no SQLite
  - listar_estoque_completo  lista tudo disponível
  - transbordo               mock: transfere para atendimento humano
"""
import logging

from langchain_core.tools import tool

from .database import buscar_produtos, formatar_produto, listar_produtos

logger = logging.getLogger(__name__)


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

    logger.info(f"🔍 Resultados encontrados: {len(produtos)} para query='{query}'")

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
    logger.info(f"🔀 TRANSBORDO acionado | motivo='{motivo}'")

    # ── MOCK ──────────────────────────────────────────────────────────────────
    # Em produção, aqui você chamaria a API do Chatwoot para:
    #   - Atribuir a conversa a um agente/equipe
    #   - Mudar o status da conversa
    #   - Disparar um webhook interno
    # Exemplo:
    #   requests.post(f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations/{conv_id}/assignments",
    #                 json={"assignee_id": AGENT_ID}, headers={"api_access_token": TOKEN})
    # ──────────────────────────────────────────────────────────────────────────

    return "TRANSBORDO_REALIZADO"


STOCK_TOOLS = [consultar_estoque, listar_estoque_completo]