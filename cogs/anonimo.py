import random
import time

import discord
from discord.ext import commands, tasks

from database.database import (
    criar_secret,
    pegar_secret,
    adicionar_resposta_secret,
    pegar_respostas_secret,
    pegar_secrets_pendentes,
    marcar_secret_publicado,
)


# Tempo padrão até as respostas do !secret serem reveladas (em minutos)
TEMPO_PADRAO_SECRET_MINUTOS = 60

# Perguntas pra quebrar o gelo — sempre em inglês e abertas de propósito,
# pra puxar mais assunto no chat
ICEBREAKERS = [
    "If you could have dinner with anyone, dead or alive, who would it be and why?",
    "What's a skill you've always wanted to learn but never had the time for?",
    "If you could live in any fictional world, which one would you choose?",
    "What's the best piece of advice you've ever received?",
    "If you could instantly become an expert in something, what would it be?",
    "What's a small thing that always makes your day better?",
    "If you had to eat one meal for the rest of your life, what would it be?",
    "What's a movie or show you could rewatch a hundred times?",
    "If you could time travel, would you go to the past or the future? Why?",
    "What's something you believed as a kid that turned out to be completely wrong?",
    "If you won the lottery tomorrow, what's the first thing you'd do?",
    "What's a hobby you picked up recently that you're really enjoying?",
    "If you could only listen to one artist for the rest of your life, who would it be?",
    "What's the most spontaneous thing you've ever done?",
    "If you could master any instrument overnight, which one would you pick?",
    "What's a place you've never been to but really want to visit?",
    "If your life had a theme song, what would it be?",
    "What's something you're really proud of, even if it's small?",
    "If you could swap lives with anyone for a day, who would it be?",
    "What's the weirdest food combination you actually enjoy?",
    "If you could give your younger self one piece of advice, what would it be?",
    "What's a game you could play for hours without getting bored?",
    "If you had an extra hour every day, how would you spend it?",
    "What's something on your bucket list you're determined to do?",
    "If you could redesign your room right now, what would you change?",
]


class Anonimo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.checar_secrets.start()


    def cog_unload(self):
        self.checar_secrets.cancel()


    # -----------------------------------------------------------------
    # !secret — cria a pergunta anônima
    # -----------------------------------------------------------------
    @commands.command(name="secret")
    async def secret(self, ctx, *, conteudo: str = None):
        if not conteudo:
            await ctx.send(
                "❌ Use assim: `!secret <sua pergunta>`\n"
                "Ou defina um tempo customizado: `!secret <minutos> <pergunta>`"
            )
            return

        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

        # Permite customizar o tempo: "!secret 30 Qual seu maior medo?"
        minutos = TEMPO_PADRAO_SECRET_MINUTOS
        pergunta = conteudo

        partes = conteudo.split(" ", 1)
        if len(partes) == 2 and partes[0].isdigit():
            minutos = max(1, int(partes[0]))
            pergunta = partes[1]

        if not pergunta.strip():
            await ctx.send("❌ Sua pergunta não pode ficar vazia.", delete_after=8)
            return

        agora = int(time.time())
        publica_em = agora + minutos * 60

        secret_id = criar_secret(
            ctx.guild.id if ctx.guild else None,
            ctx.channel.id,
            ctx.author.id,
            pergunta,
            agora,
            publica_em,
        )

        embed = discord.Embed(
            title=f"🤫 Anonymous Secret #{secret_id}",
            description=(
                f"**{pergunta}**\n\n"
                "Someone in this server wants to know! Answer anonymously below."
            ),
            color=discord.Color.purple(),
        )

        embed.add_field(
            name="Como responder",
            value=(
                f"`!answer {secret_id} <sua resposta>`\n"
                "(sua mensagem é apagada automaticamente — ninguém vai saber quem respondeu)"
            ),
            inline=False,
        )

        embed.set_footer(
            text=f"As respostas serão reveladas em {minutos} minuto(s)"
        )

        await ctx.send(embed=embed)


    # -----------------------------------------------------------------
    # !answer — responde um secret anonimamente
    # -----------------------------------------------------------------
    @commands.command(name="answer")
    async def answer(self, ctx, secret_id: int = None, *, resposta: str = None):
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

        if secret_id is None or not resposta or not resposta.strip():
            await self._avisar(ctx, "❌ Use assim: `!answer <id> <sua resposta>`")
            return

        secret = pegar_secret(secret_id)

        if secret is None:
            await self._avisar(ctx, f"❌ Secret #{secret_id} não encontrado.")
            return

        _, _, _, _, publicado = secret

        if publicado:
            await self._avisar(
                ctx,
                f"❌ Secret #{secret_id} já foi revelado, não dá mais pra responder."
            )
            return

        registrado = adicionar_resposta_secret(
            secret_id, ctx.author.id, resposta.strip(), int(time.time())
        )

        if registrado:
            await self._avisar(ctx, f"✅ Resposta anônima registrada no Secret #{secret_id}!")
        else:
            await self._avisar(ctx, f"⚠️ Você já respondeu o Secret #{secret_id}.")


    async def _avisar(self, ctx, texto):
        """Confirma a ação sem expor quem respondeu no canal (DM, com fallback apagável)."""
        try:
            await ctx.author.send(texto)
        except discord.Forbidden:
            await ctx.send(f"{ctx.author.mention} {texto}", delete_after=8)


    # -----------------------------------------------------------------
    # Loop que revela os secrets quando o tempo acaba
    # -----------------------------------------------------------------
    @tasks.loop(minutes=1)
    async def checar_secrets(self):
        agora = int(time.time())
        pendentes = pegar_secrets_pendentes(agora)

        for secret_id, channel_id, pergunta in pendentes:
            canal = self.bot.get_channel(channel_id)

            if canal is None:
                try:
                    canal = await self.bot.fetch_channel(channel_id)
                except (discord.NotFound, discord.Forbidden):
                    marcar_secret_publicado(secret_id)
                    continue

            respostas = pegar_respostas_secret(secret_id)

            if respostas:
                lista_respostas = "\n\n".join(
                    f"**{i + 1}.** {resposta}" for i, resposta in enumerate(respostas)
                )
            else:
                lista_respostas = "😶 Ninguém respondeu esse secret."

            embed = discord.Embed(
                title=f"📣 Secret #{secret_id} revelado!",
                description=f"**Pergunta:** {pergunta}\n\n{lista_respostas}",
                color=discord.Color.purple(),
            )

            embed.set_footer(text="Todas as respostas continuam 100% anônimas")

            try:
                await canal.send(embed=embed)
            except discord.Forbidden:
                pass

            marcar_secret_publicado(secret_id)


    @checar_secrets.before_loop
    async def antes_checar_secrets(self):
        await self.bot.wait_until_ready()


    # -----------------------------------------------------------------
    # !confess — confissão anônima imediata
    # -----------------------------------------------------------------
    @commands.command(name="confess")
    async def confess(self, ctx, *, confissao: str = None):
        if not confissao or not confissao.strip():
            await ctx.send("❌ Use assim: `!confess <sua confissão>`")
            return

        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

        embed = discord.Embed(
            title="🤐 Anonymous Confession",
            description=confissao.strip(),
            color=discord.Color.dark_purple(),
        )

        embed.set_footer(
            text=f"{self.bot.user.name} • Confissões são 100% anônimas"
        )

        await ctx.send(embed=embed)


    # -----------------------------------------------------------------
    # !question — pergunta aleatória pra quebrar o gelo
    # -----------------------------------------------------------------
    @commands.command(name="question")
    async def question(self, ctx):
        pergunta = random.choice(ICEBREAKERS)

        embed = discord.Embed(
            title="💬 Icebreaker Question",
            description=pergunta,
            color=discord.Color.teal(),
        )

        embed.set_footer(text=f"{self.bot.user.name} • Vamos bater um papo!")

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Anonimo(bot))
