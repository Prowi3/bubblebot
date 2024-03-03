import sys
from discord.ext import commands

@commands.command()
async def update(ctx):
    await ctx.channel.send("updating...")
    sys.exit(0)

def setup(bot):
    bot.add_command(update)