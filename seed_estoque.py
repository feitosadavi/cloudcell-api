"""
Script de seed: popula o banco com produtos de exemplo.

Uso DENTRO do container:
  docker compose exec bot python /app/seed_estoque.py
"""
import os
import sys
from pathlib import Path

# Aponta para /app para que "from app.database" funcione
sys.path.insert(0, str(Path(__file__).parent.parent))

if "DB_PATH" not in os.environ:
    os.environ["DB_PATH"] = "/app/data/estoque.db"

db_path = Path(os.environ["DB_PATH"])
db_path.parent.mkdir(parents=True, exist_ok=True)
print(f"📂 Usando banco: {db_path.resolve()}")

from app.database import init_db, inserir_produto  # noqa: E402

PRODUTOS = [
    {"nome": "IPHONE 13",        "armazenamento": "128GB", "imei": "356808582277873", "cor": "PRETO",  "tipo": "SEMINOVO", "valor": 2150.00, "bateria": "89%",  "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 13",        "armazenamento": "256GB", "imei": "356808582277874", "cor": "BRANCO", "tipo": "SEMINOVO", "valor": 2350.00, "bateria": "91%",  "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14",        "armazenamento": "128GB", "imei": "356808582277875", "cor": "AZUL",   "tipo": "SEMINOVO", "valor": 3200.00, "bateria": "95%",  "estado": "SEMINOVO", "qtd": 2},
    {"nome": "SAMSUNG GALAXY S23","armazenamento": "128GB", "imei": "356808582277876", "cor": "PRETO",  "tipo": "SEMINOVO", "valor": 1800.00, "bateria": "87%",  "estado": "SEMINOVO", "qtd": 1},
    {"nome": "SAMSUNG GALAXY A54","armazenamento": "256GB", "imei": "356808582277877", "cor": "VERDE",  "tipo": "NOVO",     "valor": 1400.00, "bateria": "100%", "estado": "NOVO",     "qtd": 3},
    {"nome": "MOTOROLA EDGE 40", "armazenamento": "256GB", "imei": "356808582277878", "cor": "PRETO",  "tipo": "NOVO",     "valor": 1600.00, "bateria": "100%", "estado": "NOVO",     "qtd": 2},
]

if __name__ == "__main__":
    init_db()
    inseridos = 0
    for p in PRODUTOS:
        try:
            pid = inserir_produto(p)
            print(f"✅ Inserido: {p['nome']} {p['armazenamento']} {p['cor']} (id={pid})")
            inseridos += 1
        except Exception as e:
            print(f"⚠️  Ignorado (já existe?): {p['nome']} — {e}")
    print(f"\n🎉 Seed concluído! {inseridos}/{len(PRODUTOS)} produtos inseridos.")