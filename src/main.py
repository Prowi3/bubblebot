import os, sys
import discord
import random
from discord.ext import commands, tasks


prefix = "bb "
intents = discord.Intents.all()
activity = discord.Game(name='')
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

@tasks.loop(seconds=5)
async def change_status():
  await bot.change_presence(activity=discord.Game(random.choice(["Poker", "it's joever"])))
        

bot.run(os.environ["TOKEN"])
