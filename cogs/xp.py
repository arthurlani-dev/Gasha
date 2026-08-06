import random
import time

import discord
from discord.ext import commands

from database.database import (
    criar_usuario,
    pegar_usuario,
    adicionar_xp,
    atualizar_level
)


class XP(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.cooldown = {}


    @commands.Cog.listener()
    async def on_message(self, message):

        # Ignora mensagens do próprio bot
        if message.author.bot:
            return


        usuario = message.author

        criar_usuario(usuario.id)


        # Cooldown de XP (60 segundos)
        agora = time.time()

        ultimo_xp = self.cooldown.get(usuario.id, 0)


        if agora - ultimo_xp < 60:
            return


        self.cooldown[usuario.id] = agora


        # XP aleatório
        xp_ganho = random.randint(15, 30)


        adicionar_xp(
            usuario.id,
            xp_ganho
        )


        dados = pegar_usuario(usuario.id)

        level, xp, pixels, conquistas = dados


        # Sistema de level
        xp_necessario = level * 1000


        if xp >= xp_necessario:

            novo_level = level + 1

            pixels_ganho = 100


            atualizar_level(
                usuario.id,
                novo_level,
                pixels_ganho
            )


            await message.channel.send(
                f"🎉 {usuario.mention} subiu para o **Level {novo_level}**!\n"
                f"💎 Você ganhou **{pixels_ganho} Pixels**!"
            )


async def setup(bot):
    await bot.add_cog(XP(bot))