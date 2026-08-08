import discord
from discord.ext import commands


class Ajuda(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="commands")
    async def commands_list(self, ctx):
        embed = discord.Embed(
            title="📜 Gasha Commands",
            description="Here's everything you can do:",
            color=discord.Color.blurple(),
        )

        embed.add_field(
            name="⭐ Profile",
            value="`!status` — shows your level, XP and pixels on this server",
            inline=False,
        )

        embed.add_field(
            name="💎 Economy",
            value=(
                "`!daily` — claim your daily pixels on the website\n"
                "`!work` — work and earn pixels (1h cooldown)\n"
                "`!leaderstats` — leaderboard of users with the most pixels"
            ),
            inline=False,
        )

        embed.add_field(
            name="🤝 Friends",
            value=(
                "`!friend @user` — send a friend request\n"
                "`!ship @user` — ship yourself with someone\n"
                "`!ship @user1 @user2` — ship two people together"
            ),
            inline=False,
        )

        embed.add_field(
            name="🎉 Mini-games",
            value=(
                "`!party` — see all available mini-games\n"
                "`!wouldyourather` — random Would You Rather question\n"
                "`!twotruths` — play Two Truths and a Lie"
            ),
            inline=False,
        )

        embed.add_field(
            name="🤫 Anonymous",
            value=(
                "`!secret <question>` — ask an anonymous question "
                "(answers revealed in 1h by default, or `!secret <minutes> <question>`)\n"
                "`!answer <id> <answer>` — answer a secret anonymously\n"
                "`!confess <text>` — confess something anonymously\n"
                "`!question` — random icebreaker question"
            ),
            inline=False,
        )

        embed.set_footer(
            text=f"{self.bot.user.name} • Levels are local to each server, but pixels are valid across all of Gasha!",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None,
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Ajuda(bot))
