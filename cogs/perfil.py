import discord
from discord.ext import commands

from database.database import (
    criar_usuario,
    pegar_usuario
)


class Perfil(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def perfil(self, ctx):

        usuario = ctx.author

        criar_usuario(usuario.id)

        dados = pegar_usuario(usuario.id)

        level, xp, pixels, conquistas = dados


        if conquistas:
            lista_conquistas = conquistas.replace(
                ",",
                "\n"
            )
        else:
            lista_conquistas = "Nenhuma conquista ainda 😢"


        # Barra de XP
        tamanho = 10

        progresso = int(
            (xp % 1000) / 1000 * tamanho
        )

        barra = (
            "🟦" * progresso +
            "⬜" * (tamanho - progresso)
        )


        embed = discord.Embed(
            title=f"Perfil de {usuario.display_name}",
            color=discord.Color.blurple()
        )


        embed.set_thumbnail(
            url=usuario.avatar.url
        )


        embed.set_image(
            url="https://i.imgur.com/SEU_BANNER.png"
        )


        embed.add_field(
            name="⭐ Level",
            value=f"`{level}`",
            inline=True
        )


        embed.add_field(
            name="✨ XP",
            value=f"`{xp}`\n{barra}",
            inline=True
        )


        embed.add_field(
            name="💎 Pixels",
            value=f"`{pixels}`",
            inline=True
        )


        embed.add_field(
            name="🏆 Conquistas",
            value=lista_conquistas,
            inline=False
        )


        embed.set_footer(
            text=f"Solicitado por {ctx.author.display_name}"
        )


        await ctx.send(embed=embed)



async def setup(bot):
    await bot.add_cog(Perfil(bot))