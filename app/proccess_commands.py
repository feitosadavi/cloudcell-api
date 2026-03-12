from app.services.agents_cache import agents_cache
from app.services.produtos_service import ProdutosService
from .evolution import EvolutionClient
from app.services.bot_service import BotService

bot_service = BotService()

produtos = ProdutosService()


HELP = """
📚 *Lista de comandos*

👑 Admin
/admin listar
/admin add <telefone>
/admin del <telefone>

📦 Estoque
/estoque listar
/estoque imei <IMEI>

🤖 Bot
/bot ver — mostra as instruções atuais do bot
/bot set <texto> — altera as instruções do bot

➕ Criar produto
/estoque criar nome=IPHONE13 armazenamento=128GB imei=123 valor=3200 qtd=1

➕➖ Ajustar estoque
/estoque ajustar <IMEI> -1

🚫 Desativar
/estoque desativar <IMEI>

🗑 Deletar
/estoque deletar <IMEI>
"""


async def proccess_commands(texto: str, phone: str, evolution_client: EvolutionClient):

    if not texto.startswith("/"):
        return None

    partes = texto.split()

    if len(partes) == 0:
        return None

    comando = partes[0]
    response = None

    # verifica admin apenas uma vez
    is_admin = agents_cache.is_admin(phone)

    # ─────────────────────────
    # HELP
    # ─────────────────────────

    if comando == "/comandos":
        response = HELP

    # ─────────────────────────
    # BOT
    # ─────────────────────────
    elif comando == "/bot":

        if not is_admin:
            response = "⛔ Apenas admins podem alterar o bot"

        else:

            if len(partes) < 2:
                response = "Use:\n/bot ver\n/bot set <texto>\n/bot reset"

            else:

                cmd = partes[1]

                if cmd == "ver":

                    instr = bot_service.get_prompt()
                    print("INSTRUÇÕES ATUAIS DO BOT:", instr)
                    response = (
                        "🤖 *Instruções atuais do bot*\n\n"
                        f"{instr}"
                    )

                elif cmd == "set":

                    if len(partes) < 3:
                        response = "⚠️ Informe o texto\n/bot set <instruções>"

                    else:

                        novo = texto.split(" ", 2)[2]

                        await bot_service.set_instructions(novo)

                        response = "✅ Instruções do bot atualizadas"

                elif cmd == "reset":

                    await bot_service.reset_instructions()

                    response = "🔄 Instruções do bot restauradas para o padrão"

                else:
                    response = "⚠️ Use /bot ver, /bot set ou /bot reset"

    # ─────────────────────────
    # ADMIN
    # ─────────────────────────

    elif comando == "/admin":

        if not is_admin:
            response = "⛔ Você não é admin"

        else:

            if len(partes) < 2:
                response = HELP

            else:

                cmd = partes[1]

                if cmd == "listar":

                    admins = agents_cache.admin_phones

                    if not admins:
                        response = "Nenhum admin cadastrado"

                    else:
                        response = "👑 *Admins*\n\n" + "\n".join(admins)

                elif cmd == "add":

                    if len(partes) < 3:
                        response = "⚠️ Informe o telefone\nUse /comandos"

                    else:

                        phone_add = partes[2]

                        agents_cache.add_admin(phone_add)

                        response = f"✅ Admin adicionado:\n{phone_add}"

                elif cmd == "del":

                    if len(partes) < 3:
                        response = "⚠️ Informe o telefone\nUse /comandos"

                    else:

                        phone_remove = partes[2]

                        agents_cache.remove_admin(phone_remove)

                        response = f"❌ Admin removido:\n{phone_remove}"

                else:
                    response = "⚠️ Comando não encontrado. Use /admin listar, /admin add ou /admin del ou /comandos"

    # ─────────────────────────
    # ESTOQUE
    # ─────────────────────────

    elif comando == "/estoque":

        if not is_admin:
            response = "⛔ Apenas admins podem usar estoque"

        else:

            if len(partes) < 2:
                response = HELP

            else:

                cmd = partes[1]

                # LISTAR
                if cmd == "listar":

                    data = produtos.listar()

                    if not data:
                        response = "📦 Estoque vazio"

                    else:

                        lines = ["📦 *Estoque:*"]

                        for p in data:

                            lines.append(
                                f"{p['nome']} ({p.get('armazenamento','')})\nIMEI: {p['imei']} | Qtd: {p['qtd']}"
                            )

                        response = "\n\n".join(lines)

                # IMEI
                elif cmd == "imei":

                    if len(partes) < 3:
                        response = "⚠️ Informe o IMEI\nUse /comandos"

                    else:

                        imei = partes[2]

                        produto = produtos.obter(imei)

                        if not produto:
                            response = "❌ Produto não encontrado"

                        else:
                            response = produtos.formatar(produto)

                # CRIAR
                elif cmd == "criar":

                    try:

                        kv = dict(x.split("=") for x in partes[2:])

                        if "imei" not in kv:
                            response = "⚠️ É obrigatório informar IMEI"

                        else:

                            if "qtd" not in kv:
                                kv["qtd"] = 1

                            produtos.inserir(kv)

                            response = f"✅ Produto criado\nIMEI: {kv['imei']}"

                    except Exception:
                        response = "⚠️ Erro ao criar produto. Use /comandos"

                # AJUSTAR
                elif cmd == "ajustar":

                    if len(partes) < 4:
                        response = "⚠️ Use /comandos"

                    else:

                        imei = partes[2]

                        try:
                            delta = int(partes[3])

                        except ValueError:
                            response = "⚠️ Quantidade inválida"

                        else:

                            produto = produtos.ajustar_estoque(imei, delta)

                            if not produto:
                                response = "❌ Produto não encontrado"

                            else:

                                response = (
                                    f"📦 Estoque atualizado\n\n"
                                    f"{produto['nome']}\n"
                                    f"IMEI: {produto['imei']}\n"
                                    f"Qtd: {produto['qtd']}"
                                )

                # DESATIVAR
                elif cmd == "desativar":

                    if len(partes) < 3:
                        response = "⚠️ Use /comandos"

                    else:

                        imei = partes[2]

                        produto = produtos.desativar(imei)

                        if not produto:
                            response = "❌ Produto não encontrado"

                        else:
                            response = f"🚫 Produto desativado\nIMEI: {imei}"

                # DELETAR
                elif cmd == "deletar":

                    if len(partes) < 3:
                        response = "⚠️ Use /comandos"

                    else:

                        imei = partes[2]

                        ok = produtos.deletar(imei)

                        if not ok:
                            response = "❌ Produto não encontrado"

                        else:
                            response = f"🗑 Produto deletado\nIMEI: {imei}"

                else:
                    response = "⚠️ Comando não encontrado. Use /produtos listar, /produtos imei <IMEI>, /produtos criar, /produtos ajustar, /produtos desativar ou /produtos deletar ou /comandos"

    # ─────────────────────────
    # DESCONHECIDO
    # ─────────────────────────

    else:
        response = "⚠️ Comando não encontrado. Use /comandos"

    # ─────────────────────────
    # ENVIO FINAL
    # ─────────────────────────

    if response is None:
        return None

    try:
        await evolution_client.send_message(
            number=phone,
            message=response
        )

    except Exception:
        pass

    return response