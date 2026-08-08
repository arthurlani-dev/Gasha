import random
import time

import discord
from discord.ext import commands

from database.database import (
    criar_usuario,
    pegar_estado_work,
    registrar_work,
    obter_leaderboard_pixels,
)


# Link do resgate diário no site (o !daily do bot só avisa e leva pra cá,
# quem realmente credita os pixels é o site em web/app.py)
DAILY_URL = "https://gasha.up.railway.app/daily"

# Cooldown do !work em segundos (1 hora)
COOLDOWN_WORK = 60 * 60

# Faixa de pixels ganhos por !work
WORK_PIXELS_MIN = 15
WORK_PIXELS_MAX = 50

# Pequenas "falas" aleatórias pro !work não ficar sempre igual
TAREFAS_WORK = [
    "organizou os arquivos do servidor",
    "ajudou um novato a configurar o Discord",
    "moderou o chat com maestria",
    "testou um novo comando do bot",
    "desenhou uma pixel art pra comunidade",
    "respondeu dúvidas no suporte",
]


class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="daily")
    async def daily(self, ctx):
        embed = discord.Embed(
            title="💎 Daily Pixels",
            description=(
                "Daily pixels aren't claimed here on Discord!\n\n"
                f"Head over to the website and [Click here!]({DAILY_URL}) "
                "to log in and claim today's reward."
            ),
            color=discord.Color.blue()
        )

        embed.set_footer(
            text=f"{self.bot.user.name} • Daily Reward",
            icon_url=self.bot.user.avatar.url
            if self.bot.user.avatar else None
        )

        await ctx.send(embed=embed)


    @commands.command(name="work")
    async def work(self, ctx):
        usuario = ctx.author

        # Garante que o usuário existe no banco
        criar_usuario(usuario.id)

        estado = pegar_estado_work(usuario.id)
        ultimo_work = estado[0] if estado else 0

        agora = int(time.time())

        if ultimo_work:
            restante = COOLDOWN_WORK - (agora - ultimo_work)

            if restante > 0:
                minutos = restante // 60
                segundos = restante % 60

                await ctx.send(
                    f"⏳ {usuario.mention}, você já trabalhou recentemente! "
                    f"Tente novamente em **{minutos}m {segundos}s**."
                )
                return

        pixels_ganhos = random.randint(WORK_PIXELS_MIN, WORK_PIXELS_MAX)
        registrar_work(usuario.id, agora, pixels_ganhos)

        tarefa = random.choice(TAREFAS_WORK)

        embed = discord.Embed(
            description=(
                f"💼 {usuario.mention} {tarefa} e ganhou "
                f"**{pixels_ganhos} 💎 pixels**!"
            ),
            color=discord.Color.green()
        )

        await ctx.send(embed=embed)


    @commands.command(name="leaderstats")
    async def leaderstats(self, ctx):
        top = obter_leaderboard_pixels(10)

        if not top:
            await ctx.send("❌ Ainda não há dados suficientes para o ranking.")
            return

        medalhas = ["🥇", "🥈", "🥉"]
        linhas = []

        for i, (user_id, pixels) in enumerate(top):
            try:
                usuario = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                nome = usuario.display_name if hasattr(usuario, "display_name") else usuario.name
            except discord.NotFound:
                nome = f"Usuário {user_id}"

            posicao = medalhas[i] if i < 3 else f"`#{i + 1}`"
            linhas.append(f"{posicao} **{nome}** — 💎 {pixels}")

        embed = discord.Embed(
            title="🏆 Leaderstats — Pixels",
            description="\n".join(linhas),
            color=discord.Color.gold()
        )

        embed.set_footer(
            text=f"{self.bot.user.name} • Ranking de Pixels",
            icon_url=self.bot.user.avatar.url
            if self.bot.user.avatar else None
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Economia(bot))
