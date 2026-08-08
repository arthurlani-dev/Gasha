import random
import time

import discord
from discord.ext import commands

from database.database import (
    criar_usuario,
    pegar_perfil,
    adicionar_xp,
    subir_level,
    incrementar_estatistica,
)


class XP(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.cooldown = {}


    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return


        user_id = message.author.id


        criar_usuario(user_id)


        agora = time.time()

        ultimo = self.cooldown.get(user_id, 0)


        if agora - ultimo < 60:
            return


        self.cooldown[user_id] = agora


        xp_ganho = random.randint(10, 25)


        adicionar_xp(
            user_id,
            xp_ganho
        )

        # Conta como interação para a seção "Em números" do site
        # (contador antigo só somava comandos de prefixo, então ficava
        # zerado — mensagens com XP são a interação real e mais comum).
        incrementar_estatistica("comandos_executados")


        perfil = pegar_perfil(user_id)


        _, level, xp, pixels, conquistas = perfil


        xp_necessario = level * 1000


        if xp >= xp_necessario:

            subir_level(user_id)


            embed = discord.Embed(
                description=(
                    f"🎉 Parabéns, {message.author.mention}! Você subiu para o "
                    f"**nível {level + 1}** neste servidor!"
                ),
                color=discord.Color.gold()
            )

            embed.set_footer(
                text="📍 Níveis são locais de cada servidor — mas seus 💎 pixels valem em todo o Gasha!"
            )

            await message.channel.send(embed=embed)



async def setup(bot):
    await bot.add_cog(XP(bot))
