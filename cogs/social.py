import asyncio
import random
import time

import discord
from discord.ext import commands

from database.database import sao_amigos, adicionar_amizade


class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # -----------------------------------------------------------------
    # !friend — envia um pedido de amizade que o outro precisa aceitar
    # -----------------------------------------------------------------
    @commands.command(name="friend")
    async def friend(self, ctx, membro: discord.Member = None):
        if membro is None:
            await ctx.send("❌ Usage: `!friend @user`")
            return

        if membro.id == ctx.author.id:
            await ctx.send("❌ You can't add yourself as a friend!")
            return

        if membro.bot:
            await ctx.send("❌ You can't add a bot as a friend!")
            return

        if sao_amigos(ctx.author.id, membro.id):
            await ctx.send(f"You're already friends with {membro.mention}!")
            return

        embed = discord.Embed(
            title="🤝 Friend Request",
            description=(
                f"{membro.mention}, {ctx.author.mention} wants to be your friend!\n\n"
                "React with ✅ to accept or ❌ to decline."
            ),
            color=discord.Color.green(),
        )

        mensagem = await ctx.send(embed=embed)
        await mensagem.add_reaction("✅")
        await mensagem.add_reaction("❌")

        def checar(reaction, user):
            return (
                reaction.message.id == mensagem.id
                and user.id == membro.id
                and str(reaction.emoji) in ("✅", "❌")
            )

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=checar)
        except asyncio.TimeoutError:
            await ctx.send(f"⌛ The friend request to {membro.mention} has expired.")
            return

        if str(reaction.emoji) == "✅":
            adicionar_amizade(ctx.author.id, membro.id, int(time.time()))
            await ctx.send(f"🎉 {ctx.author.mention} and {membro.mention} are now friends!")
        else:
            await ctx.send(f"{membro.mention} declined the friend request.")


    # -----------------------------------------------------------------
    # !ship — shipa duas pessoas (ou você com alguém, se só um @ for dado)
    # -----------------------------------------------------------------
    @commands.command(name="ship")
    async def ship(self, ctx, membro1: discord.Member = None, membro2: discord.Member = None):
        if membro1 is None:
            await ctx.send("❌ Usage: `!ship @user` or `!ship @user1 @user2`")
            return

        if membro2 is None:
            pessoa_a = ctx.author
            pessoa_b = membro1
        else:
            pessoa_a = membro1
            pessoa_b = membro2

        if pessoa_a.id == pessoa_b.id:
            await ctx.send("❌ You can't ship someone with themselves!")
            return

        # Semente fixa pela dupla: o mesmo par sempre dá a mesma porcentagem
        semente = pessoa_a.id + pessoa_b.id
        porcentagem = random.Random(semente).randint(0, 100)

        metade_a = pessoa_a.display_name[: max(1, len(pessoa_a.display_name) // 2)]
        metade_b = pessoa_b.display_name[len(pessoa_b.display_name) // 2:]
        nome_shippado = metade_a + metade_b

        coracoes_cheios = porcentagem // 10
        barra = "❤️" * coracoes_cheios + "🖤" * (10 - coracoes_cheios)

        if porcentagem >= 80:
            comentario = "A match made in heaven! 💍"
        elif porcentagem >= 50:
            comentario = "There's definitely something here! 👀"
        elif porcentagem >= 20:
            comentario = "Eh... could work with a bit of effort. 😅"
        else:
            comentario = "Yeah... maybe just stay friends. 💀"

        embed = discord.Embed(
            title=f"💘 {pessoa_a.display_name} + {pessoa_b.display_name}",
            description=(
                f"**{nome_shippado}**\n\n"
                f"{barra}\n"
                f"**{porcentagem}%** compatible\n\n"
                f"{comentario}"
            ),
            color=discord.Color.red(),
        )

        if pessoa_a.avatar:
            embed.set_thumbnail(url=pessoa_a.avatar.url)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Social(bot))
