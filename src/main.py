import os
import discord
import io
import random


from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont


prefix = "bb "

intents = discord.Intents.all()

bot = commands.Bot(prefix, intents=intents, activity=discord.Game(name="Poker"))


@bot.event
async def on_ready():
    os.system("clear")
    print(bot.user)

@bot.command()
async def hello(ctx):
    await ctx.send("Hello !")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.lower() == "poke":
        await message.channel.send("Hey Don't Do That! >:(", reference=message)
    await bot.process_commands(message)

#error log

@bot.event
async def on_command_error(ctx, error):
    channel_id = 1142387860650082334
    chan = bot.get_channel(channel_id)
    
    embed = discord.Embed(
        title=f'Command Error in {ctx.command}',
        description=str(error),
        color=discord.Color(int("0xAA698F", 16))
    )
    
    await chan.send(embed=embed)



bot.run(os.environ["TOKEN"])
