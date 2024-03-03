import os, sys
from discord.ext import commands

@commands.command()
async def update(ctx):
    await ctx.channel.send("Rebooting...")
    os.execv(sys.executable, ['python'] + sys.argv)

def setup(bot):
    bot.add_command(update)