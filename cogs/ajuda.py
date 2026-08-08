import discord
from discord.ext import commands


class Ajuda(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="commands")
    async def commands_list(self, ctx):
        embed = discord.Embed(
            title="📜 Comandos do Gasha",
            description="Aqui está tudo que você pode fazer por aqui:",
            color=discord.Color.blurple(),
        )

        embed.add_field(
            name="⭐ Perfil",
            value="`!status` — mostra seu level, XP e pixels neste servidor",
            inline=False,
        )

        embed.add_field(
            name="💎 Economia",
            value=(
                "`!daily` — resgate seus pixels diários no site\n"
                "`!work` — trabalhe e ganhe pixels (cooldown de 1h)\n"
                "`!leaderstats` — ranking dos usuários com mais pixels"
            ),
            inline=False,
        )

        embed.add_field(
            name="🤫 Social & Anônimo",
            value=(
                "`!secret <pergunta>` — faça uma pergunta anônima "
                "(respostas reveladas em 1h por padrão, ou `!secret <minutos> <pergunta>`)\n"
                "`!answer <id> <resposta>` — responda um secret anonimamente\n"
                "`!confess <texto>` — confesse algo anonimamente\n"
                "`!question` — pergunta aleatória pra quebrar o gelo"
            ),
            inline=False,
        )

        embed.set_footer(
            text=f"{self.bot.user.name} • Levels são locais de cada servidor, mas pixels valem em todo o Gasha!",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None,
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Ajuda(bot))
