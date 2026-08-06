import os
import discord

from discord.ext import commands
from dotenv import load_dotenv

from database.database import criar_tabelas


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


bot.run(TOKEN)