"""
Script de seed: popula o banco com a lista real de iPhones.
"""
import os
import sys
from pathlib import Path

# Ajuste de path para importação do app
sys.path.insert(0, str(Path(__file__).parent))

if "DB_PATH" not in os.environ:
    os.environ["DB_PATH"] = "/app/data/estoque.db"

from app.database import init_db, inserir_produto

PRODUTOS = [
    {"nome": "IPHONE 11", "armazenamento": "128GB", "imei": "357883119561502", "cor": "BRANCO", "tipo": "SEMINOVO", "valor": 850.00, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},

    {"nome": "IPHONE 12", "armazenamento": "128GB", "imei": "352113536322972", "cor": "BRANCO", "tipo": "SEMINOVO", "valor": 700.00, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 12 PRO", "armazenamento": "128GB", "imei": "356462524195502", "cor": "GRAFITE", "tipo": "SEMINOVO", "valor": 1600.00, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},

    {"nome": "IPHONE 13", "armazenamento": "128GB", "imei": "356646220828883", "cor": "BRANCO", "tipo": "SEMINOVO", "valor": 1700, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 13", "armazenamento": "128GB", "imei": "355317934149716", "cor": "BRANCO", "tipo": "SEMINOVO", "valor": 1800, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 13", "armazenamento": "128GB", "imei": "355017388948007", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 1800, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 13", "armazenamento": "128GB", "imei": "352991733892149", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 1700, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},

    {"nome": "IPHONE 13 PRO", "armazenamento": "256GB", "imei": "350753240822775", "cor": "AZUL SIERRA", "tipo": "SEMINOVO", "valor": 2500, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 13 PRO", "armazenamento": "256GB", "imei": "358823345895281", "cor": "AZUL SIERRA", "tipo": "SEMINOVO", "valor": 2500, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 13 PRO", "armazenamento": "256GB", "imei": "354509715280212", "cor": "CINZA", "tipo": "SEMINOVO", "valor": 2500, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 13 PRO", "armazenamento": "256GB", "imei": "359349739810123", "cor": "SIERRA", "tipo": "SEMINOVO", "valor": 2500, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 13 PRO", "armazenamento": "256GB", "imei": "354509714792036", "cor": "CINZA", "tipo": "SEMINOVO", "valor": 2500, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 13 PRO", "armazenamento": "256GB", "imei": "354509714792035", "cor": "CINZA", "tipo": "SEMINOVO", "valor": 2500, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 13 PRO", "armazenamento": "256GB", "imei": "352668911856845", "cor": "CINZA", "tipo": "SEMINOVO", "valor": 2500, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},

    {"nome": "IPHONE 13 PRO MAX", "armazenamento": "128GB", "imei": "359836513659007", "cor": "VERDE", "tipo": "SEMINOVO", "valor": 2580.0, "bateria": 83, "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 13 PRO MAX", "armazenamento": "128GB", "imei": "356189752960279", "cor": "GRAFITE", "tipo": "SEMINOVO", "valor": 2580.0, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 13 PRO MAX", "armazenamento": "128GB", "imei": "356622129221900", "cor": "GRAFITE", "tipo": "SEMINOVO", "valor": 2580.0, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 13 PRO MAX", "armazenamento": "128GB", "imei": "350879907131976", "cor": "GRAFITE", "tipo": "SEMINOVO", "valor": 2580.0, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 13 PRO MAX", "armazenamento": "128GB", "imei": "357680889144752", "cor": "GRAFITE", "tipo": "SEMINOVO", "valor": 2580.0, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 13 PRO MAX", "armazenamento": "128GB", "imei": "354106777270023", "cor": "GRAFITE", "tipo": "SEMINOVO", "valor": 2580.0, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 13 PRO MAX", "armazenamento": "128GB", "imei": "355380250621833", "cor": "GRAFITE", "tipo": "SEMINOVO", "valor": 2580.0, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 13 PRO MAX", "armazenamento": "128GB", "imei": "350566102366149", "cor": "GRAFITE", "tipo": "SEMINOVO", "valor": 2600.0, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},

    {"nome": "IPHONE 14", "armazenamento": "256GB", "imei": "355111145746976", "cor": "VERMELHO", "tipo": "SEMINOVO", "valor": 2050, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    
    {"nome": "IPHONE 14 PLUS", "armazenamento": "128GB", "imei": "356752985658026", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 2200, "bateria": "84%", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PLUS", "armazenamento": "128GB", "imei": "356485671802422", "cor": "VERMELHO", "tipo": "SEMINOVO", "valor": 0.0, "bateria": "84%", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PLUS", "armazenamento": "128GB", "imei": "359069336554185", "cor": "LILÁS", "tipo": "SEMINOVO", "valor": 0.0, "bateria": "85%", "estado": "SEMINOVO", "qtd": 1},
    
    {"nome": "IPHONE 14 PRO", "armazenamento": "128GB", "imei": "353501802004507", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 2800, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PRO", "armazenamento": "128GB", "imei": "359128129224495", "cor": "ROXO", "tipo": "SEMINOVO", "valor": 2800, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PRO", "armazenamento": "128GB", "imei": "352228701985492", "cor": "ROXO", "tipo": "SEMINOVO", "valor": 2750, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PRO", "armazenamento": "128GB", "imei": "353664576217877", "cor": "ROXO", "tipo": "SEMINOVO", "valor": 2750, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PRO", "armazenamento": "128GB", "imei": "358996913991334", "cor": "ROXO", "tipo": "SEMINOVO", "valor": 2750, "bateria": "63%", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PRO", "armazenamento": "128GB", "imei": "353664570578126", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 2750, "bateria": "63%", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PRO", "armazenamento": "128GB", "imei": "358073467514399", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 2750, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    
    {"nome": "IPHONE 14 PRO MAX", "armazenamento": "256GB", "imei": "350813223907397", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 3250, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PRO MAX", "armazenamento": "128GB", "imei": "357938435882634", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 3250, "bateria": "74%", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PRO MAX", "armazenamento": "256GB", "imei": "353427811457199", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 3250, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PRO MAX", "armazenamento": "256GB", "imei": "357938435153176", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 3250, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PRO MAX", "armazenamento": "256GB", "imei": "355086752291427", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 3250, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PRO MAX", "armazenamento": "256GB", "imei": "355901945133866", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 3250, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PRO MAX", "armazenamento": "256GB", "imei": "352051379540468", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 3250, "bateria": "81%", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PRO MAX", "armazenamento": "256GB", "imei": "350813223958333", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 3250, "bateria": "81%", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PRO MAX", "armazenamento": "256GB", "imei": "353427815558349", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 3250, "bateria": "81%", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PRO MAX", "armazenamento": "256GB", "imei": "357938437905912", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 3250, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 14 PRO MAX", "armazenamento": "256GB", "imei": "351446987910551", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 3250, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},

    {"nome": "IPHONE 15", "armazenamento": "128GB", "imei": "356321250463387", "cor": "VERDE", "tipo": "SEMINOVO", "valor": 2900, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},

    {"nome": "IPHONE 15 PRO", "armazenamento": "256GB", "imei": "353864161645959", "cor": "AZUL TITANIUM", "tipo": "SEMINOVO", "valor": 3750.0, "bateria": "87%", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 15 PRO", "armazenamento": "256GB", "imei": "353431659593552", "cor": "BLACK/GRAY", "tipo": "SEMINOVO", "valor": 3750.0, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 15 PRO", "armazenamento": "256GB", "imei": "354070968155544", "cor": "AZUL TITANIUM", "tipo": "SEMINOVO", "valor": 3750.0, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 15 PRO", "armazenamento": "256GB", "imei": "353431653540179", "cor": "TITANIUM AZUL", "tipo": "SEMINOVO", "valor": 3850.0, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 15 PRO", "armazenamento": "256GB", "imei": "356611841314499", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 3850.0, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    
    {"nome": "IPHONE 15 PRO MAX", "armazenamento": "256GB", "imei": "351503405288745", "cor": "AZUL TITANIUM", "tipo": "SEMINOVO", "valor": 4100.00, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 15 PRO MAX", "armazenamento": "256GB", "imei": "350496301486060", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 4100.00, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 15 PRO MAX", "armazenamento": "256GB", "imei": "356371484825299", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 4100.00, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 15 PRO MAX", "armazenamento": "256GB", "imei": "351016867751779", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 4100.00, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
    {"nome": "IPHONE 15 PRO MAX", "armazenamento": "256GB", "imei": "352832406914580", "cor": "PRETO", "tipo": "SEMINOVO", "valor": 4100.00, "bateria": "N/I", "estado": "SEMINOVO", "qtd": 1},
]

if __name__ == "__main__":
    init_db()
    inseridos = 0
    for p in PRODUTOS:
        try:
            inserir_produto(p)
            print(f"✅ {p['nome']} ({p['cor']}) inserido.")
            inseridos += 1
        except Exception as e:
            print(f"❌ Erro no {p['nome']} {p['imei']}: {e}")
    
    print(f"\nFinalizado! {inseridos} produtos no estoque.")