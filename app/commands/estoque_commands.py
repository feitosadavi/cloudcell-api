from services.command_router import command


@command("estoque")
async def help_estoque(ctx):

    await ctx.reply(
"""
Comandos estoque:

/estoque.buscar iphone 13
/estoque.imei <imei>
/estoque.listar
/estoque.criar nome=IPHONE valor=3200 qtd=2
/estoque.ajustar <id> -1
/estoque.desativar <id>
/estoque.deletar <id>
"""
    )


@command("estoque.buscar")
async def buscar(ctx, *query):

    query = " ".join(query)

    res = await ctx.api.buscar(query)

    linhas = []

    for p in res:
        linhas.append(f"{p['id']} {p['nome']} qtd={p['qtd']}")

    await ctx.reply("\n".join(linhas))


@command("estoque.listar")
async def listar(ctx):

    res = await ctx.api.listar()

    linhas = []

    for p in res:
        linhas.append(f"{p['id']} {p['nome']} qtd={p['qtd']}")

    await ctx.reply("\n".join(linhas))


@command("estoque.ajustar")
async def ajustar(ctx, pid, delta):

    r = await ctx.api.ajustar(pid, int(delta))

    await ctx.reply(f"Novo estoque: {r['qtd']}")


@command("estoque.desativar")
async def desativar(ctx, pid):

    await ctx.api.desativar(pid)

    await ctx.reply("Produto desativado")


@command("estoque.deletar")
async def deletar(ctx, pid):

    await ctx.api.deletar(pid)

    await ctx.reply("Produto deletado permanentemente")
