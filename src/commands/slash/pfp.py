import discord
from discord import option
from discord.ext import commands

class Pfp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="pfp", description="Sends the Profile Picture of the User that you select")
    @option("user", description="blahblah")
    async def pfp(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        pfp_url = user.avatar.url
        embed = discord.Embed(title=f"Profile Picture of {user.display_name}", color=0x9FC6F6)
        embed.set_image(url=pfp_url)
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Pfp(bot))
