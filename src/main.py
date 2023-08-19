import os, sys
import discord


from discord.ext import commands
from PIL import Image, ImageDraw


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
        await message.channel.send("Hey Don't Do That! >:(", reference=message)
    await bot.process_commands(message)


@bot.command()
async def test(ctx):
    img = Image.new("RGB", (1080, 1080), color="white")
    draw = ImageDraw.Draw(img)
    img_path = "image.png"
    img.save(img_path)

    with open(img_path, "rb") as img_file:
        await ctx.send(file=discord.File(img_file))

bot.run(os.environ["TOKEN"])
