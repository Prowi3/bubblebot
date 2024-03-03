from discord.ext import commands

@commands.command()
async def update(ctx):
    await ctx.send("i'll add it later i swear")

def setup(bot):
    bot.add_command(update)
