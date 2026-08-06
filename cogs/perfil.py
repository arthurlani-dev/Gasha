import discord
from discord.ext import commands

from database.database import (
    criar_usuario,
    pegar_usuario
)


class Perfil(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="perfil")
    async def perfil(self, ctx):

        usuario = ctx.author

        criar_usuario(usuario.id)

        dados = pegar_usuario(usuario.id)

        level, xp, pixels, conquistas = dados


        if conquistas:
            lista_conquistas = conquistas.replace(",", "\n")
        else:
            lista_conquistas = "Nenhuma conquista ainda 😢"


        # Barra de XP
        tamanho_barra = 10

        progresso = int(
            ((xp % 1000) / 1000) * tamanho_barra
        )

        barra_xp = (
            "🟦" * progresso +
            "⬜" * (tamanho_barra - progresso)
        )


        embed = discord.Embed(
            title=f"👤 Perfil de {usuario.display_name}",
            color=discord.Color.blurple()
        )


        if usuario.avatar:
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
            value=f"`{xp}`\n{barra_xp}",
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
            text=f"{self.bot.user.name} • Sistema de Perfil"
        )


        await ctx.send(embed=embed)



async def setup(bot):
    await bot.add_cog(Perfil(bot))
    print("Cog Perfil carregado!")