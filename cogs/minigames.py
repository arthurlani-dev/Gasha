import random

import discord
from discord.ext import commands


WOULD_YOU_RATHER = [
    ("have the ability to fly", "have the ability to become invisible"),
    ("always be 10 minutes late", "always be 20 minutes early"),
    ("live without music", "live without movies"),
    ("be able to talk to animals", "be able to speak every human language"),
    ("have unlimited money", "have unlimited free time"),
    ("never use social media again", "never watch another movie or show"),
    ("be famous", "be super rich but unknown"),
    ("always know when someone is lying", "always be able to get away with lying"),
    ("live in space", "live under the ocean"),
    ("lose your sense of smell", "lose your sense of taste"),
    ("be the funniest person in the room", "be the smartest person in the room"),
    ("travel to the past", "travel to the future"),
    ("never have to sleep again", "never have to eat again"),
    ("have a rewind button for your life", "have a pause button for your life"),
    ("be able to teleport anywhere", "be able to read minds"),
    ("live in a world with no internet", "live in a world with no cars"),
    ("only be able to whisper", "only be able to shout"),
    ("have a personal chef", "have a personal driver"),
    ("give up your phone for a year", "give up your favorite food for a year"),
    ("be able to control fire", "be able to control water"),
]

ICEBREAKER_MINIGAMES = [
    (
        "🤔 `!wouldyourather`",
        "Get a random Would You Rather question with two options",
    ),
    (
        "🎭 `!twotruths`",
        "Play Two Truths and a Lie — post 3 statements separated by `|` and let people guess the lie",
    ),
    (
        "💘 `!ship`",
        "Ship two people (or yourself with someone) and see the compatibility",
    ),
    (
        "💬 `!question`",
        "Get a random icebreaker question to spark conversation",
    ),
]


class Minigames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="party")
    async def party(self, ctx):
        embed = discord.Embed(
            title="🎉 Mini-games",
            description="Here's everything you can play with friends:",
            color=discord.Color.magenta(),
        )

        for nome, descricao in ICEBREAKER_MINIGAMES:
            embed.add_field(name=nome, value=descricao, inline=False)

        embed.set_footer(text=f"{self.bot.user.name} • Pick one and have fun!")

        await ctx.send(embed=embed)


    @commands.command(name="wouldyourather")
    async def wouldyourather(self, ctx):
        opcao_a, opcao_b = random.choice(WOULD_YOU_RATHER)

        embed = discord.Embed(
            title="🤔 Would You Rather...",
            description=f"**A)** {opcao_a}\n\n**B)** {opcao_b}",
            color=discord.Color.orange(),
        )

        mensagem = await ctx.send(embed=embed)
        await mensagem.add_reaction("🇦")
        await mensagem.add_reaction("🇧")


    @commands.command(name="twotruths")
    async def twotruths(self, ctx, *, conteudo: str = None):
        if not conteudo:
            await ctx.send(
                "❌ Usage: `!twotruths <statement 1> | <statement 2> | <statement 3>`\n"
                "Make two of them true and one a lie! Example:\n"
                "`!twotruths I've been to Japan | I hate pizza | I can play the guitar`"
            )
            return

        partes = [p.strip() for p in conteudo.split("|") if p.strip()]

        if len(partes) != 3:
            await ctx.send(
                "❌ You need exactly 3 statements separated by `|`. Example:\n"
                "`!twotruths I've been to Japan | I hate pizza | I can play the guitar`"
            )
            return

        embed = discord.Embed(
            title=f"🎭 Two Truths and a Lie — {ctx.author.display_name}",
            description=(
                f"**1)** {partes[0]}\n"
                f"**2)** {partes[1]}\n"
                f"**3)** {partes[2]}\n\n"
                "Which one is the lie? React below to guess!"
            ),
            color=discord.Color.blurple(),
        )

        mensagem = await ctx.send(embed=embed)
        for emoji in ("1️⃣", "2️⃣", "3️⃣"):
            await mensagem.add_reaction(emoji)


async def setup(bot):
    await bot.add_cog(Minigames(bot))
