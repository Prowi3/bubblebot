import os, sys
import discord


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
    img_size = 1080
    grid_size = 10
    square_size = img_size // grid_size

    img = Image.new("RGB", (img_size, img_size), color="white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default() 

    num = 1
    for i in range(grid_size):
        for j in range(grid_size):
            square_coords = (i * square_size, j * square_size)
            square_end_coords = (square_coords[0] + square_size, square_coords[1] + square_size)
            draw.rectangle((square_coords, square_end_coords), outline="black", width=3)
            text_width, text_height = draw.textsize(str(num), font=font)
            text_position = ((square_coords[0] + square_end_coords[0] - text_width) // 2, (square_coords[1] + square_end_coords[1] - text_height) // 2)
            draw.text(text_position, str(num), fill="black", font=font)
            num += 1


bot.run(os.environ["TOKEN"])
