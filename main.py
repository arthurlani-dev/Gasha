import os
import discord

from discord.ext import commands
from dotenv import load_dotenv

from database.database import (
    criar_tabelas,
    definir_estatistica,
    incrementar_estatistica,
)


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")


intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


criar_tabelas()


@bot.event
async def setup_hook():
    await bot.load_extension("cogs.perfil")
    await bot.load_extension("cogs.xp")


@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")

    # Atualiza a contagem de servidores exibida no site (seção "Em números")
    definir_estatistica("servidores", len(bot.guilds))


@bot.event
async def on_guild_join(guild):
    definir_estatistica("servidores", len(bot.guilds))


@bot.event
async def on_guild_remove(guild):
    definir_estatistica("servidores", len(bot.guilds))


@bot.event
async def on_command_completion(ctx):
    # Toda vez que um comando roda com sucesso, soma no contador global do site
    incrementar_estatistica("comandos_executados")


bot.run(TOKEN)
