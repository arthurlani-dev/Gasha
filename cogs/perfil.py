import discord
from discord.ext import commands

from database.database import criar_usuario, pegar_usuario


class Perfil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="perfil")
    async def perfil(self, ctx):
        usuario = ctx.author

        # Garante que o usuário existe no banco
        criar_usuario(usuario.id)

        # Busca os dados
        dados = pegar_usuario(usuario.id)

        if dados is None:
            await ctx.send("❌ Não foi possível encontrar seu perfil.")
            return

        level, xp, pixels, conquistas = dados


        # Formatação das conquistas
        if conquistas:
            conquistas_formatadas = conquistas.replace(",", "\n")
        else:
            conquistas_formatadas = "🔒 Nenhuma conquista desbloqueada"


        # Barra de XP
        xp_proximo_level = 1000

        progresso = int(
            (xp % xp_proximo_level) / xp_proximo_level * 10
        )

        barra_xp = (
            "🟦" * progresso +
            "⬜" * (10 - progresso)
        )


        # Criando embed
        embed = discord.Embed(
            title=f"✨ Perfil de {usuario.display_name}",
            description=f"Confira as informações de {usuario.mention}",
            color=discord.Color.blurple()
        )


        # Avatar
        if usuario.avatar:
            embed.set_thumbnail(
                url=usuario.avatar.url
            )


        # Informações principais
        embed.add_field(
            name="⭐ Level",
            value=f"```{level}```",
            inline=True
        )

        embed.add_field(
            name="✨ XP",
            value=f"```{xp}```\n{barra_xp}",
            inline=True
        )

        embed.add_field(
            name="💎 Pixels",
            value=f"```{pixels}```",
            inline=True
        )


        # Conquistas
        embed.add_field(
            name="🏆 Conquistas",
            value=conquistas_formatadas,
            inline=False
        )


        # Banner do perfil (troque depois pela imagem do bot)
        embed.set_image(
            url="https://i.imgur.com/SEU_BANNER.png"
        )


        embed.set_footer(
            text=f"{self.bot.user.name} • Sistema de Perfil",
            icon_url=self.bot.user.avatar.url
            if self.bot.user.avatar else None
        )


        await ctx.send(embed=embed)



async def setup(bot):
    await bot.add_cog(Perfil(bot))