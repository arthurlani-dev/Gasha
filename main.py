import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

intents = discord.Intents.all()
bot = commands.Bot("!", intents=intents)

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f"Logado como {client.user}")

client.run(TOKEN)