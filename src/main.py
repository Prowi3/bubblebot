import os, sys
import discord
from discord.ext import commands


prefix = "bb "
intents = discord.Intents.all()
intents.typing = False
intents.presences = False
activity = discord.Game(name='Playing Poker')
bot = commands.Bot(prefix, intents=intents, activity=None, status=None)

@bot.event
async def on_ready():
  os.system("clear")
  print(bot.user)

@bot.command()
async def hello(ctx):
  await ctx.send("Hello !")

@bot.command()
async def bye(ctx):
  await ctx.channel.typing()
  os.remove("BOTCONDITION")
  sys.exit(0)

@bot.command()
async def update(ctx):
  await ctx.channel.send('booting up....')
  sys.exit(0)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.lower() == "poke":
        await message.channel.send("poke", reference=message)
    await bot.process_commands(message)

@bot.event
async def one_ready():
    server_id = 1139938006824923136
    channel_id = 1139987677668724827

    server = bot.get_guild(server_id)
    channel = bot.get_channel(channel_id)

    await channel.send("Bubble is Ready")
    

bot.run(os.environ["TOKEN"])
