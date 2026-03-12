import logging
from rapidfuzz import fuzz, process

from app.database import db

logger = logging.getLogger(__name__)


class ProdutosService:

    # ─────────────────────────
    # CREATE
    # ─────────────────────────

    def inserir(self, dados: dict):

        with db() as conn:

            conn.execute(
                """
                INSERT INTO produtos (
                    nome, armazenamento, imei, cor, tipo,
                    valor, bateria, estado, qtd
                )
                VALUES (
                    :nome, :armazenamento, :imei, :cor, :tipo,
                    :valor, :bateria, :estado, :qtd
                )
                """,
                dados
            )

        return dados["imei"]

    # ─────────────────────────
    # READ
    # ─────────────────────────

    def obter(self, imei: str):

        with db() as conn:

            row = conn.execute(
                "SELECT * FROM produtos WHERE imei = ?",
                (imei,)
            ).fetchone()

        return dict(row) if row else None

    def listar(self, apenas_disponiveis=True):

        where = "WHERE qtd > 0 AND ativo = 1" if apenas_disponiveis else ""

        with db() as conn:

            rows = conn.execute(
                f"""
                SELECT * FROM produtos
                {where}
                ORDER BY nome, armazenamento
                """
            ).fetchall()

        return [dict(r) for r in rows]

    # ─────────────────────────
    # UPDATE
    # ─────────────────────────

    def atualizar(self, imei: str, dados: dict):

        campos = {
            "nome", "armazenamento", "cor", "tipo",
            "valor", "bateria", "estado", "qtd", "ativo"
        }

        updates = {k: v for k, v in dados.items() if k in campos}

        if not updates:
            return self.obter(imei)

        set_clause = ", ".join(f"{k} = :{k}" for k in updates)

        updates["imei"] = imei

        with db() as conn:

            conn.execute(
                f"""
                UPDATE produtos
                SET {set_clause}
                WHERE imei = :imei
                """,
                updates
            )

        return self.obter(imei)

    # ─────────────────────────
    # ESTOQUE
    # ─────────────────────────

    def ajustar_estoque(self, imei: str, delta: int):

        with db() as conn:

            row = conn.execute(
                "SELECT qtd FROM produtos WHERE imei = ?",
                (imei,)
            ).fetchone()

            if not row:
                return None

            nova_qtd = max(0, row["qtd"] + delta)

            conn.execute(
                "UPDATE produtos SET qtd = ? WHERE imei = ?",
                (nova_qtd, imei)
            )

        return self.obter(imei)

    # ─────────────────────────
    # DELETE
    # ─────────────────────────

    def deletar(self, imei: str):

        with db() as conn:

            affected = conn.execute(
                "DELETE FROM produtos WHERE imei = ?",
                (imei,)
            ).rowcount

        return affected > 0

    def desativar(self, imei: str):

        with db() as conn:

            conn.execute(
                "UPDATE produtos SET ativo = 0, qtd = 0 WHERE imei = ?",
                (imei,)
            )

        return self.obter(imei)

    # ─────────────────────────
    # BUSCA FUZZY
    # ─────────────────────────

    def buscar_produtos(query: str, limite: int = 5, score_minimo: int = 40) -> list[dict]:
        """
        1. Busca TODOS os produtos ativos com qtd > 0
        2. Aplica fuzzy search (rapidfuzz WRatio) sobre nome+armazenamento+cor+tipo+estado
        3. Retorna os `limite` melhores acima do score_minimo
        """
        query_clean = query.strip()

        # Passo 1: traz tudo do banco
        with db() as conn:
            rows = conn.execute(
                "SELECT * FROM produtos WHERE qtd > 0 AND ativo = 1"
            ).fetchall()

        produtos = [dict(r) for r in rows]
        if not produtos:
            return []

        # Passo 2: monta chave textual de cada produto para comparação
        def chave(p: dict) -> str:
            return " ".join(filter(None, [
                p.get("nome", ""), p.get("armazenamento", ""),
                p.get("cor", ""), p.get("tipo", ""), p.get("estado", ""),
            ])).upper()

        q = query_clean.upper()
        chaves = [chave(p) for p in produtos]

        # Passo 3: fuzzy scoring com scorer combinado
        # token_set_ratio: "iphone" vs "IPHONE 13 128GB PRETO" → score alto (imune a strings longas)
        # partial_ratio:   encontra a query dentro da string maior
        # Usa o maior dos dois para máxima cobertura
        def scorer_combinado(s1, s2, **kwargs):
            return max(
                fuzz.token_set_ratio(s1, s2),
                fuzz.partial_ratio(s1, s2),
            )

        resultados = process.extract(
            q, chaves,
            scorer=scorer_combinado,
            limit=limite,
            score_cutoff=score_minimo,
        )

        indices_scores = sorted(
            [(idx, score) for _, score, idx in resultados],
            key=lambda x: x[1], reverse=True
        )
        return [produtos[idx] for idx, _ in indices_scores]

    # ─────────────────────────
    # FORMATAR
    # ─────────────────────────

    def formatar(self, p: dict):

        valor = "N/A"

        if p.get("valor"):
            valor = f"R$ {p['valor']:,.2f}"
            valor = valor.replace(",", "X").replace(".", ",").replace("X", ".")

        return (
            f"📱 *{p['nome']}*\n"
            f"Armazenamento: {p.get('armazenamento','N/A')}\n"
            f"Cor: {p.get('cor','N/A')}\n"
            f"Tipo: {p.get('tipo','N/A')}\n"
            f"Estado: {p.get('estado','N/A')}\n"
            f"Bateria: {p.get('bateria','N/A')}\n"
            f"💰 {valor}\n"
            f"📦 Qtd: {p.get('qtd',0)}\n"
            f"IMEI: {p.get('imei','N/A')}"
        )