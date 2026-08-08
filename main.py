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

TOKEN = os.getenv("DISCORD_TOKEN", "").strip() or None


intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


criar_tabelas()


@bot.event
async def setup_hook():
    await bot.load_extension("cogs.status")
    await bot.load_extension("cogs.xp")
    await bot.load_extension("cogs.economia")


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
    # Toda vez que um comando de prefixo (!perfil, etc.) roda com sucesso,
    # soma no contador global do site
    incrementar_estatistica("comandos_executados")


@bot.event
async def on_app_command_completion(interaction, command):
    # Mesmo contador, mas para slash commands (/daily, /top, etc.)
    # quando você adicionar app_commands aos cogs
    incrementar_estatistica("comandos_executados")


bot.run(TOKEN)
