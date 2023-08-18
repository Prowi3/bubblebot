import discord
import random
import os
import io
import httpx
import math
import asyncio
import requests
import aiohttp
from discord.ext import tasks
from discord.ext import commands
from always_on import keep_alive
from PIL import Image, ImageDraw, ImageFont

intents = discord.Intents.default()

bot = commands.Bot("bb ", intents=discord.Intents.all())

@bot.remove_command("help")

#prefix commands:

#1- bb hello

@bot.command()
async def hello(ctx):
    await ctx.send("Hello!")

#2- bb help

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="BubbleBot Help",
        description="BubbleBot Commands:",
        color=discord.Color(0xAA698F)
    )
    items = [
        ("Fun Commands:", "totally fun"),
        ("1- /bruhinator", "use when bruh moment."),
        ("2- /draw", "get a randomly generated image."),
        ("3- /number_guess", "Guess the randomly generated number!"),
        ("4- /tictactoe", "play a game of tictactoe! use /restart to restart the board.(unstable at the moment)"),
        ("5- /cta", "get a random picture of a cat."),
        ("6- /2ball", "get an answer for any questions"),
        ("Support Commands:", "No support command will be added to BubbleBot due to the high risk")
         ]


    for index, (item_name, item_description) in enumerate(items, start=1):
        embed.add_field(name=item_name, value=item_description, inline=False)
    
 
    await ctx.send(embed=embed)

#ON Message commands

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
#Bubble Call
    if message.content.lower() == "bubble":
        await message.channel.send("GUH!!!!", reference=message)
#Poke
    if message.content.lower() == "poke":
        file = open("Text Files/poke.txt", "r")
        content = file.read()
        all_lines = content.splitlines( )
        output = random.choice(all_lines) 
        await message.channel.send(output, reference=message)
#Mentions
    if message.content.lower() == "<@1131529056882524212>":
        await message.channel.send("RAAAAAAAAAH!!!!", reference=message)
#Reply
    if message.reference:
        replied_message = message.reference.resolved
        if replied_message.author == bot.user:
            await message.channel.trigger_typing()
            await message.reply("indeed ")

    await bot.process_commands(message)

#Slash Commands

#1- Help

@bot.slash_command(name="help", description = "bubblebot command list")
async def show_list(ctx):
    embed = discord.Embed(
        title="BubbleBot Help",
        description="BubbleBot Commands:",
        color=discord.Color(0xAA698F)
    )
    items = [
        ("Fun Commands:", "totally fun"),
        ("1- /bruhinator", "use when bruh moment."),
        ("2- /draw", "get a randomly generated image."),
        ("3- /number_guess", "Guess the randomly generated number!"),
        ("4- /tictactoe", "play a game of tictactoe! use /restart to restart the board.(unstable at the moment)"),
        ("5- /cta", "get a random picture of a cat."),
        ("6- /2ball", "get an answer for any questions"),
        ("Support Commands:", "No support command will be added to BubbleBot due to the high risk")
    ]

    for index, (item_name, item_description) in enumerate(items, start=1):
        embed.add_field(name=item_name, value=item_description, inline=False)
    
 
    await ctx.respond(embed=embed)

#2- BruhMoment

@bot.slash_command(name="bruhinator", description = "Use When Bruh Moment")
async def bruh(ctx): 
    file = open("Text Files/bruh.txt", "r")
    content = file.read()
    all_lines = content.splitlines( )
    output = random.choice(all_lines) 
    await ctx.respond(output)

#3- 2Ball (thx to daWUM)

@bot.slash_command(name="2ball", description = "ANY QUESTION ANSWERER")
async def twoball(interaction, question: str):
  twoballanswer = ["My answer is yes", "My answer is no"]
  await interaction.response.send_message(f"Question: '{question}'\n{random.choice(twoballanswer)}")

#4- Number Guessing

@bot.slash_command(name="number_guess", description="Guess the randomly generated number!")
async def guess_the_number(ctx):
    await ctx.respond("Guess a number between 1-100")

    random_number = random.randint(1, 100)
    num_guesses = 0

    try:
        guess = await bot.wait_for("message", timeout=30, check=lambda m: m.author == ctx.author)

        while True:
            num_guesses += 1
            user_guess = int(guess.content)

            if user_guess == random_number:
                await ctx.send(f"Congratulations, {ctx.author.mention}! You guessed the number {random_number} in {num_guesses} guesses.")
                break
            elif user_guess < random_number:
                await ctx.send("Higher! Guess again.")
            else:
                await ctx.send("Lower! Guess again.")

            guess = await bot.wait_for("message", timeout=15, check=lambda m: m.author == ctx.author)

    except asyncio.TimeoutError:
        await ctx.send(f"Time's up! The correct number was {random_number}.")
    
#5- Draw Command

@bot.slash_command(name="draw", description="generate a random drawing")
async def draw(ctx):
    width, height = 1440, 1440
    image = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(image)

    for _ in range(25):
        choice = random.choice(["line", "circle", "triangle"])

        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        if choice == "line":
            x1 = random.randint(0, width - 1)
            y1 = random.randint(0, height - 1)
            x2 = random.randint(0, width - 1)
            y2 = random.randint(0, height - 1)
            draw.line((x1, y1, x2, y2), fill=color, width=random.randint(1, 20))

        elif choice == "circle":
            center_x = random.randint(0, width - 1)
            center_y = random.randint(0, height - 1)
            radius = random.randint(10, 200)
            draw.ellipse(
                (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
                outline=color,
                width=random.randint(1, 10)
            )

        elif choice == "triangle":
            x1 = random.randint(0, width - 1)
            y1 = random.randint(0, height - 1)
            x2 = random.randint(0, width - 1)
            y2 = random.randint(0, height - 1)
            x3 = random.randint(0, width - 1)
            y3 = random.randint(0, height - 1)
            draw.polygon([(x1, y1), (x2, y2), (x3, y3)], outline=color, width=random.randint(1, 10))

    image.save("random.png")
    await ctx.respond(file=discord.File("random.png"))

#6- TicTacToe + restart Command (

def initialize_board():
    return [" " for _ in range(9)]

board = initialize_board()
current_player = "X"

def check_winner():
    for i in range(0, 9, 3):
        if board[i] == board[i+1] == board[i+2] != " ":
            return board[i]
    for i in range(3):
        if board[i] == board[i+3] == board[i+6] != " ":
            return board[i]
    if board[0] == board[4] == board[8] != " ":
        return board[0]
    if board[2] == board[4] == board[6] != " ":
        return board[2]
    return None

@bot.slash_command(name="tictactoe", description="Play a game of Tic Tac Toe")
async def tictactoe(ctx, move: int ):
    global board, current_player
    
    move -= 1
    
    if 0 <= move < 9 and board[move] == " ":
        board[move] = current_player
        
        winner = check_winner()
        if winner:
            winning_indices = []
            for i in range(9):
                if board[i] == winner:
                    winning_indices.append(i)
            
            image = Image.new('RGB', (300, 300), 'black')
            draw = ImageDraw.Draw(image)
            
            win_color = (255, 0, 0)
            font = ImageFont.truetype("Montserrat-SemiBold.ttf", 60)
            
            for i, cell in enumerate(board):
                row = i // 3
                col = i % 3
                x = col * 100
                y = row * 100

                square_size = 90
                square_x = x + 5
                square_y = y + 5
                draw.rectangle([square_x, square_y, square_x + square_size, square_y + square_size], outline="grey", width=5)
                
                if cell != " ":
                    text_bbox = draw.textbbox((x, y), cell, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    text_x = x + (square_size - text_width) // 2 + 5
                    text_y = y + (square_size - text_height) // 2 - 10
                    if i in winning_indices:
                        draw.text((text_x, text_y), cell, fill=win_color, font=font)
                    else:
                        draw.text((text_x, text_y), cell, fill='white', font=font)
                else:
                    empty_cell_number = str(i + 1)
                    text_bbox = draw.textbbox((x, y), empty_cell_number, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    text_x = x + (square_size - text_width) // 2 + 5
                    text_y = y + (square_size - text_height) // 2 - 10
                    draw.text((text_x, text_y), empty_cell_number, fill='grey', font=font)
            
            image_bytes = io.BytesIO()
            image.save(image_bytes, format='PNG')
            image_bytes.seek(0)
            
            await ctx.respond(content=f"Player {winner} wins!", file=discord.File(fp=image_bytes, filename='tictactoe_board.png'))

            board = initialize_board()
            return
        
        current_player = "O" if current_player == "X" else "X"
        
        image = Image.new('RGB', (300, 300), 'black')
        draw = ImageDraw.Draw(image)
        
        font = ImageFont.truetype("Montserrat-SemiBold.ttf", 60)
        
        for i, cell in enumerate(board):
            row = i // 3
            col = i % 3
            x = col * 100
            y = row * 100

            square_size = 90
            square_x = x + 5
            square_y = y + 5
            draw.rectangle([square_x, square_y, square_x + square_size, square_y + square_size], outline="grey", width=5)
            
            if cell != " ":
                text_bbox = draw.textbbox((x, y), cell, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                text_x = x + (square_size - text_width) // 2 + 5
                text_y = y + (square_size - text_height) // 2 - 10
                draw.text((text_x, text_y), cell, fill='white', font=font)
            else:
                empty_cell_number = str(i + 1)
                text_bbox = draw.textbbox((x, y), empty_cell_number, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                text_x = x + (square_size - text_width) // 2 + 5
                text_y = y + (square_size - text_height) // 2 - 10
                draw.text((text_x, text_y), empty_cell_number, fill='grey', font=font)
            
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes.seek(0)
        
        await ctx.respond(content=f"Player {current_player}'s turn:", file=discord.File(fp=image_bytes, filename='tictactoe_board.png'))
    else:
        await ctx.respond(content="Invalid move. Please choose an unoccupied cell between 1 and 9.")
      
@bot.slash_command(name="restart", description="Restart the Tic Tac Toe game")
async def restart(ctx):
    global board, current_player
    board = initialize_board()
    current_player = "X"
    await ctx.respond(content="the game has been restarted")
                   
#7-cta posting command

@bot.slash_command(name="cta", description="Send a random cta picture")
async def random_cat(ctx):
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.thecatapi.com/v1/images/search")
        if response.status_code == 200:
            data = response.json()
            cta_url = data[0]["url"]
            await ctx.respond(content="Here's a random cta picture:" + cta_url)
        else:
            await ctx.send("Failed to find cta :(")

#Slash Command Testing
#gif testing

@bot.slash_command(name="test", description="possible .gif experimentation")
async def rotating_line(ctx):
    num, w, h, line_length, frame_rate, f = 100, 400, 400, 400, 100, []

    for i in range(num):
        a = i * (360 / num)
        x, y = w // 2, h // 2
        image = Image.new('RGB', (w, h), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        angle_rad = math.radians(a)
        end_x = x + int(line_length * math.cos(angle_rad))
        end_y = y - int(line_length * math.sin(angle_rad))
        
        draw.line((x, y, end_x, end_y), fill=(0, 0, 0), width=2)
        f.append(image)

    io_out = io.BytesIO()
    f[0].save(io_out, format='GIF', save_all=True, append_images=f[1:], duration=frame_rate, loop=0)
    io_out.seek(0)
    await ctx.respond(file=discord.File(fp=io_out, filename='rotating_line.gif'))

#always on (thx to Haku), token

@bot.event
async def on_ready():
    print("Ready")
    print(f"logged as {bot.user}")
    change_status.start()


@tasks.loop(seconds=5)
async def change_status():
  await bot.change_presence(activity=discord.Game(random.choice(["/help | bb help", "hey don't do that ?¿"])))

bot.run(os.environ['TOKEN'])
