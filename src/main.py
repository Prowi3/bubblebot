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

bot.command()
async def test(ctx):
    img_size = 1080
    grid_size = 10
    square_size = img_size // grid_size

    img = Image.new("RGB", (img_size, img_size), color="black")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    num = 1
    for i in range(grid_size):
        for j in range(grid_size):
            square_coords = (i * square_size, j * square_size)
            square_end_coords = (square_coords[0] + square_size, square_coords[1] + square_size)
            draw.rectangle((square_coords, square_end_coords), outline="white", width=3)
            text = str(num)
            text_size = draw.textsize(text, font=font)
            text_position = (
                square_coords[0] + (square_size - text_size[0]) // 2,
                square_coords[1] + (square_size - text_size[1]) // 2,
            )
            draw.text(text_position, text, fill="grey", font=font)
            num += 1

    image_bytes = io.BytesIO()
    img.save(image_bytes, format='PNG')
    image_bytes.seek(0)

    await ctx.send(file=discord.File(image_bytes, filename='grid.png'))



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
