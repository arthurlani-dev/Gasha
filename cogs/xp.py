import random
import time

from discord.ext import commands

from database.database import (
    criar_usuario,
    pegar_perfil,
    adicionar_xp,
    subir_level
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


        perfil = pegar_perfil(user_id)


        _, level, xp, pixels, conquistas = perfil


        xp_necessario = level * 1000


        if xp >= xp_necessario:

            subir_level(user_id)


            await message.channel.send(
                f"🎉 {message.author.mention} subiu para o nível **{level + 1}**!"
            )



async def setup(bot):
    await bot.add_cog(XP(bot))