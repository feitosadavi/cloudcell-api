import re
import httpx
import os
import os
import logging

INVENTORY_BASE = os.getenv("INVENTORY_BASE")

client = httpx.AsyncClient(timeout=20)

HELP = """
Comandos disponíveis:
/estoque comandos
/estoque listar_todos
/estoque buscar <texto>
/estoque buscar_por_imei <IMEI>
/estoque criar nome=IPHONE valor=3200 qtd=2
/estoque ajustar <IMEI|id> <delta>
/estoque desativar <IMEI|id>
/estoque deletar_permanente <IMEI|id>
"""

async def buscar(query):
    r = await client.get(f"{INVENTORY_BASE}/buscar", params={"q": query})
    r.raise_for_status()
    return r.json()

async def listar():
    r = await client.get(f"{INVENTORY_BASE}/")
    r.raise_for_status()
    return r.json()

async def criar(data):
    r = await client.post(f"{INVENTORY_BASE}/", json=data)
    r.raise_for_status()
    return r.json()

async def ajustar(pid, delta):
    r = await client.patch(f"{INVENTORY_BASE}/{pid}/estoque", json={"delta": delta})
    r.raise_for_status()
    return r.json()

async def desativar(pid):
    r = await client.delete(f"{INVENTORY_BASE}/{pid}")
    r.raise_for_status()
    return r.json()

async def deletar(pid):
    r = await client.delete(f"{INVENTORY_BASE}/{pid}/permanente")
    r.raise_for_status()
    return r.json()


async def executar_comando(texto: str):

    texto = texto.strip()

    if not texto.startswith("/estoque"):
        return None

    partes = texto.split()
    if len(partes) == 1:
        return HELP

    cmd = partes[1]

    if cmd == "comandos":
        return HELP

    if cmd == "listar_todos":
        data = await listar()
        items = data.get("items", data)

        resposta = []
        for p in items:
            resposta.append(f"{p['id']} {p['nome']} qtd={p['qtd']}")

        return "\n".join(resposta)

    if cmd == "buscar":
        query = " ".join(partes[2:])
        data = await buscar(query)

        resposta = []
        for p in data:
            resposta.append(f"{p['id']} {p['nome']} qtd={p['qtd']}")

        return "\n".join(resposta)

    if cmd == "criar":

        kv = dict(x.split("=") for x in partes[2:])

        if "valor" in kv:
            kv["valor"] = float(kv["valor"])

        if "qtd" in kv:
            kv["qtd"] = int(kv["qtd"])

        r = await criar(kv)

        return f"Produto criado ID {r['id']}"

    if cmd == "ajustar":

        pid = partes[2]
        delta = int(partes[3])

        r = await ajustar(pid, delta)

        return f"Novo estoque: {r['qtd']}"

    if cmd == "desativar":

        pid = partes[2]

        await desativar(pid)

        return "Produto desativado"

    if cmd == "deletar_permanente":

        pid = partes[2]

        await deletar(pid)

        return "Produto deletado"

    return "Comando desconhecido"

seen_messages = set()

async def processar_webhook(payload):

    if payload.get("event") != "message_created":
        return

    message_id = payload.get("id")

    if message_id in seen_messages:
        return

    seen_messages.add(message_id)

    if payload.get("message_type") != "incoming":
        return

    texto = payload.get("content")

    conversation_id = payload["conversation"]["id"]
    account_id = payload["account"]["id"]

    resposta = await executar_comando(texto)

    if resposta:

        await send_chatwoot_reply(
            account_id,
            conversation_id,
            resposta
        )