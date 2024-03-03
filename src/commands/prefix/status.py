import os, sys
import subprocess
from discord.ext import commands

@commands.command()
async def update(ctx):
    await ctx.channel.send("Updating...")
    subprocess.run(['git', 'pull'], check=True)
    await ctx.channel.send("Update complete. Rebooting...")
    os.execv(sys.executable, ['python'] + sys.argv)

def setup(bot):
    bot.add_command(update)