from discord.ext import commands

@commands.command()
async def test(ctx):
    await ctx.send("13")

def setup(bot):
    bot.add_command(test)