import os,sys
import subprocess
from discord.ext import commands

@commands.command()
async def update(ctx, folder_name: str):
    subprocess.run(['git', 'fetch', 'origin', 'main'], check=True)
    subprocess.run(['git', 'checkout', 'origin/main', folder_name], check=True)
    await ctx.channel.send(f"Folder '{src}' updated. Rebooting...")
    os.execv(sys.executable, ['python'] + sys.argv)

def setup(bot):
    bot.add_command(update)