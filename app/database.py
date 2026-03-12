"""
Gerenciamento do banco SQLite de produtos.
Inclui FTS5 (full-text search nativo do SQLite) + fuzzy scoring via rapidfuzz.
"""
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from rapidfuzz import fuzz, process

import os

logger = logging.getLogger(__name__)

DB_PATH = Path(os.environ.get("DB_PATH", "/app/data/estoque.db"))


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Cria tabelas e FTS virtual table na primeira execução."""
    with db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS produtos (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                nome          TEXT    NOT NULL,
                armazenamento TEXT,
                imei          TEXT    UNIQUE,
                cor           TEXT,
                tipo          TEXT,
                valor         REAL,
                bateria       TEXT,
                estado        TEXT,
                qtd           INTEGER DEFAULT 1,
                ativo         INTEGER DEFAULT 1,
                created_at    TEXT    DEFAULT (datetime('now')),
                updated_at    TEXT    DEFAULT (datetime('now'))
            );
                           
            CREATE TABLE IF NOT EXISTS bot_config (
                key TEXT PRIMARY KEY,
                value TEXT
            );
                           
            CREATE TABLE IF NOT EXISTS admin_phones (
                phone TEXT PRIMARY KEY,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS produtos_fts USING fts5(
                nome,
                armazenamento,
                cor,
                tipo,
                estado,
                content='produtos',
                content_rowid='id'
            );

            CREATE TRIGGER IF NOT EXISTS produtos_ai AFTER INSERT ON produtos BEGIN
                INSERT INTO produtos_fts(rowid, nome, armazenamento, cor, tipo, estado)
                VALUES (new.id, new.nome, new.armazenamento, new.cor, new.tipo, new.estado);
            END;

            CREATE TRIGGER IF NOT EXISTS produtos_ad AFTER DELETE ON produtos BEGIN
                INSERT INTO produtos_fts(produtos_fts, rowid, nome, armazenamento, cor, tipo, estado)
                VALUES ('delete', old.id, old.nome, old.armazenamento, old.cor, old.tipo, old.estado);
            END;

            CREATE TRIGGER IF NOT EXISTS produtos_au AFTER UPDATE ON produtos BEGIN
                INSERT INTO produtos_fts(produtos_fts, rowid, nome, armazenamento, cor, tipo, estado)
                VALUES ('delete', old.id, old.nome, old.armazenamento, old.cor, old.tipo, old.estado);
                INSERT INTO produtos_fts(rowid, nome, armazenamento, cor, tipo, estado)
                VALUES (new.id, new.nome, new.armazenamento, new.cor, new.tipo, new.estado);
            END;

            CREATE TRIGGER IF NOT EXISTS produtos_updated_at AFTER UPDATE ON produtos BEGIN
                UPDATE produtos SET updated_at = datetime('now') WHERE id = new.id;
            END;
        """)
    logger.info("✅ Banco de dados inicializado.")


# ── CREATE ────────────────────────────────────────────────────────────────────

def inserir_produto(dados: dict) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO produtos (nome, armazenamento, imei, cor, tipo, valor, bateria, estado, qtd)
            VALUES (:nome, :armazenamento, :imei, :cor, :tipo, :valor, :bateria, :estado, :qtd)
        """, dados)
        return cur.lastrowid


# ── READ ──────────────────────────────────────────────────────────────────────

def obter_produto(produto_id: int) -> dict | None:
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
        return dict(row) if row else None


def listar_produtos(apenas_disponiveis: bool = True, pagina: int = 1, por_pagina: int = 50) -> dict:
    offset = (pagina - 1) * por_pagina
    with db() as conn:
        where = "WHERE qtd > 0 AND ativo = 1" if apenas_disponiveis else ""
        total = conn.execute(f"SELECT COUNT(*) FROM produtos {where}").fetchone()[0]
        rows = conn.execute(
            f"SELECT * FROM produtos {where} ORDER BY nome, armazenamento LIMIT ? OFFSET ?",
            (por_pagina, offset)
        ).fetchall()
        return {
            "total": total,
            "pagina": pagina,
            "por_pagina": por_pagina,
            "paginas": (total + por_pagina - 1) // por_pagina,
            "items": [dict(r) for r in rows],
        }


# ── UPDATE ────────────────────────────────────────────────────────────────────

def atualizar_produto(produto_id: int, dados: dict) -> dict | None:
    """Atualiza apenas os campos fornecidos (PATCH semântico)."""
    campos_permitidos = {
        "nome", "armazenamento", "imei", "cor", "tipo",
        "valor", "bateria", "estado", "qtd", "ativo",
    }
    updates = {k: v for k, v in dados.items() if k in campos_permitidos and v is not None}
    if not updates:
        return obter_produto(produto_id)

    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["id"] = produto_id

    with db() as conn:
        affected = conn.execute(
            f"UPDATE produtos SET {set_clause} WHERE id = :id", updates
        ).rowcount
        if affected == 0:
            return None
        return dict(conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone())


def ajustar_estoque(produto_id: int, delta: int) -> dict | None:
    """Incrementa (+) ou decrementa (-) a quantidade em estoque."""
    with db() as conn:
        row = conn.execute("SELECT qtd FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        if not row:
            return None
        nova_qtd = max(0, row["qtd"] + delta)
        conn.execute("UPDATE produtos SET qtd = ? WHERE id = ?", (nova_qtd, produto_id))
        return dict(conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone())


# ── DELETE ────────────────────────────────────────────────────────────────────

def deletar_produto(produto_id: int) -> bool:
    """Hard delete — remove definitivamente."""
    with db() as conn:
        affected = conn.execute(
            "DELETE FROM produtos WHERE id = ?", (produto_id,)
        ).rowcount
        return affected > 0


def desativar_produto(produto_id: int) -> dict | None:
    """Soft delete — mantém o registro mas marca como inativo."""
    with db() as conn:
        affected = conn.execute(
            "UPDATE produtos SET ativo = 0, qtd = 0 WHERE id = ?", (produto_id,)
        ).rowcount
        if affected == 0:
            return None
        return dict(conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone())


# ── ADMINS ───────────────────────────────────────────────────────────────
def listar_admins() -> list[str]:
    with db() as conn:
        rows = conn.execute("SELECT phone FROM admin_phones").fetchall()
        return [r["phone"] for r in rows]


def adicionar_admin(phone: str):
    with db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO admin_phones (phone) VALUES (?)",
            (phone,)
        )


def remover_admin(phone: str):
    with db() as conn:
        conn.execute(
            "DELETE FROM admin_phones WHERE phone = ?",
            (phone,)
        )

# ── BUSCA FUZZY ──────────────────────────────────────────────────────────────

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


def formatar_produto(p: dict) -> str:
    valor = f"R$ {p['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if p.get("valor") else "N/A"
    return (
        f"📱 *{p['nome']}*\n"
        f"   Armazenamento: {p.get('armazenamento', 'N/A')}\n"
        f"   Cor: {p.get('cor', 'N/A')}\n"
        f"   Tipo: {p.get('tipo', 'N/A')}\n"
        f"   Estado: {p.get('estado', 'N/A')}\n"
        f"   Bateria: {p.get('bateria', 'N/A')}\n"
        f"   Valor: {valor}\n"
        f"   Qtd disponível: {p.get('qtd', 0)}\n"
        f"   IMEI: {p.get('imei', 'N/A')}"
    )