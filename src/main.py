import os
import discord
import io


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

#snakes and ladders

@bot.command()
async def test(ctx):
    img_size = 800
    grid_size = 10
    square_size = img_size // grid_size

    img = Image.new("RGB", (img_size, img_size), color="white")
    draw = ImageDraw.Draw(img)

    snakes = {16: 6, 47: 26, 49: 11, 56: 53, 62: 19, 64: 60, 87: 24, 93: 73, 95: 75, 98: 78}
    ladders = {1: 38, 4: 14, 9: 31, 21: 42, 28: 84, 36: 44, 51: 67, 71: 91, 80: 100}

    for i in range(grid_size):
        for j in range(grid_size):
            x = i * square_size
            y = (grid_size - 1 - j) * square_size  # Flip y-coordinate for correct orientation
            square_coords = (x, y)
            square_end_coords = (x + square_size, y + square_size)
            draw.rectangle((square_coords, square_end_coords), outline="black", width=3)

            position = i + j * grid_size + 1  # Calculate the current position on the board
            if position in snakes:
                draw.text((x + square_size // 2, y + square_size // 2), "S", fill="red", font=None, anchor="mm")
            if position in ladders:
                draw.text((x + square_size // 2, y + square_size // 2), "L", fill="green", font=None, anchor="mm")

    img_path = "snakes_and_ladders.png"
    img.save(img_path)

    with open(img_path, "rb") as img_file:
        await ctx.send(file=discord.File(img_file))

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
