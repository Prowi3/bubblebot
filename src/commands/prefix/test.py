from discord.ext import commands

@commands.command()
async def test(ctx):
    await ctx.send("it works yay!")

def setup(bot):
    bot.add_command(test)