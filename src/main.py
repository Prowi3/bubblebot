import discord
import random
import os
import io
import httpx
import asyncio
import requests
import json
import urllib.parse
import aiohttp
import datetime
import subprocess

from discord.ext import tasks
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
from io import BytesIO
from typing import Union, Optional
from petpetgif import petpet as petpetgif
from googleapiclient.discovery import build

#subs

command = "sudo apt install firefox -y"

try:
    subprocess.run(command, shell=True, check=True)
    print("Huray!!!!!")
except subprocess.CalledProcessError as e:
    print(f"something wong: {e}")

#prefixes and command removal

prefixes = ["bb ", "bB ", "BB ", "Bb "]

bot = commands.Bot(command_prefix=prefixes, intents=discord.Intents.all())

@bot.remove_command("help")

#---------------------------------------------------------#
#                    :prefix commands:                    #
#---------------------------------------------------------#

#1- BB hello/Contact

@bot.command()
async def hello(ctx):
    await ctx.send("https://media.discordapp.net/attachments/1065649826341072999/1126008651392483509/AutoMemes.gif", reference=ctx.message)

CHANNEL_ID = 1147741557001289839

@bot.command(name="contact", aliases=["Contact"])
async def contacting(ctx, *, message):
    target_channel = bot.get_channel(CHANNEL_ID)
    
    formatted_message = f'{ctx.author.mention} says: "{message}"'

    await target_channel.send(formatted_message)

    await ctx.reply("Your message has been successfully sent!")

#2- BB help

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="BubbleBot Help",
        description="here's a list of available commands:",
        color=discord.Color(0x9FC6F6))
    
    thumbnail_url = "https://cdn.discordapp.com/attachments/1142411437688500274/1146230560205840446/output-onlinegiftools_2.gif"
    embed.set_thumbnail(url=thumbnail_url)
    
    embed.add_field(name="__**/cta**__", value="**╰→** sends a random picture of a cat", inline=True)
    embed.add_field(name="__**/draw**__", value="**╰→** sends a randomly generated pic", inline=True)
    embed.add_field(name="__**/number_guess**__", value="**╰→** guess the number within 15 seconds, type **cancel** to cancel the game", inline=True)
    embed.add_field(name="__**/not_sfw**__", value="**╰→** sends a **totally family friendly** picture based on a tag (bomb will send 5 pictures)", inline=True)
    embed.add_field(name="__**/sfw**__", value="**╰→** sends a Random **safe anmie** picture (bomb will send 5 pictures)", inline=True)
    embed.add_field(name="__**BB Search**__", value="**╰→** search for pictures using google images", inline=True)
    embed.add_field(name="__**BB Google**__", value="**╰→** same as **bb search** but higher quality (limited to 100 per day)", inline=True)
    embed.add_field(name="__**BB Moise**__", value="**╰→** sends Pictures of moise", inline=True)
    embed.add_field(name="__**BB Pfp**__", value="**╰→** sends users' profile pictures", inline=True)
    embed.add_field(name="__**BB Pet**__", value="**╰→** pet a user or a server emoji", inline=True)

    embed.set_footer(text="Feel free to reach out if you encounter any problems or have something to share by using (BB Contact)")
    
    await ctx.send(embed=embed)

#3- Bb search

sent_image_urls = set()

@bot.command(name="ser", aliases=["search"])
async def search_image(ctx, *, search_query: str):
    search_query_encoded = urllib.parse.quote(search_query)
    search_url = f"https://www.google.com/search?q={search_query_encoded}&tbm=isch&safe=active"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    img_tags = soup.find_all("img")

    image_urls = [img["src"] for img in img_tags if "src" in img.attrs and img["src"] not in sent_image_urls and not img["src"].endswith(".gif")]

    if image_urls:
        selected_image_url = random.choice(image_urls)
        sent_image_urls.add(selected_image_url)

        search_query_decoded = urllib.parse.unquote(search_query)
        embed = discord.Embed(color=0x9FC6F6, title=f"You searched for: {search_query_decoded}")
        embed.set_image(url=selected_image_url)

        await ctx.send(embed=embed)
    else:
        await ctx.send("wtf were you searching☠️.")

#4- BB moisey

@bot.command(name="moise", aliases=["Moise"])
async def moisy(ctx, number: int = None):
    if number is None:
        await ctx.send("you must specify the number of moise pics (bb moise 1)")
        return

    if number > 50:
        await ctx.send("Sorry, the maximum number is 50.")
    else:
        file = open("miscellaneous/moise.txt", "r")
        content = file.read()
        file.close()
        for _ in range(number):
            await ctx.send(content)

#5- BB say (personal)

def is_owner(ctx):
    return ctx.author.id == 1037871415187210240

@bot.command()
@commands.check(is_owner)
async def say(ctx, channel_id, *, message):
    channel = bot.get_channel(int(channel_id))
    if channel:
        await channel.send(message)
        await ctx.message.delete()
    else:
        await ctx.send("something wong")

@say.error
async def say_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("NUH UH!!!!")

#6- BB Pfp

@bot.command(name="pfp", aliases=["Pfp"])
async def pfp(ctx, user: discord.Member = None):
    user = user or ctx.author
    pfp_url = user.avatar.url
    embed = discord.Embed(title=f"Profile Picture of {user.display_name}", color=0x9FC6F6)
    embed.set_image(url=pfp_url)
    await ctx.send(embed=embed, reference=ctx.message)

#7- BB Pet

@bot.command()
async def pet(ctx, image: Optional[Union[discord.PartialEmoji, discord.Member, str]]):
    async with aiohttp.ClientSession() as session:
        if isinstance(image, discord.PartialEmoji):
            async with session.get(str(image.url)) as resp:
                image = await resp.read()
        elif isinstance(image, discord.Member):
            image = await image.avatar.read()
        elif isinstance(image, str) and image.startswith('http'):
            async with session.get(image) as resp:
                image = await resp.read()
        elif image == 'last':
            async for message in ctx.channel.history(limit=10):
                if message.attachments:
                    attachment = message.attachments[0]
                    if attachment.content_type.startswith('image/'):
                        async with session.get(attachment.url) as resp:
                            image = await resp.read()
                        break
                elif message.embeds:
                    embed = message.embeds[0]
                    if embed.image:
                        async with session.get(embed.image.url) as resp:
                            image = await resp.read()
                        break
            else:
                await ctx.reply('No recent images found in the chat.')
                return
        else:
            await ctx.reply('invalid petting :(')
            return

        source = BytesIO(image)
        dest = BytesIO()
        petpetgif.make(source, dest)
        dest.seek(0)
        await ctx.send(file=discord.File(dest, filename="petpet.gif"), reference=ctx.message)

#8- Ser V2

sent_image_links = []

@bot.command(name="gl", aliases=["google"])
async def google_image_search(ctx, *, query: str):
    global sent_image_links

    service = build("customsearch", "v1", developerKey=os.environ['GLSEARCH'])
    results = service.cse().list(
        q=query,
        cx='779432b9c976d4325',
        searchType='image',
        safe='high'
    ).execute()

    if 'items' in results and len(results['items']) > 0:
        image_links = [item['link'] for item in results['items']]
        
        new_image_links = [link for link in image_links if link not in sent_image_links]
        
        if not new_image_links:
            await ctx.send("No new images found.")
            return

        random_image_link = random.choice(new_image_links)
        sent_image_links.append(random_image_link)
        
        embed = discord.Embed(title=f"You searched for: {query}", color=0x9FC6F6)
        embed.set_image(url=random_image_link)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("Stop searching for weird shit please")

#test

@bot.command()
async def gradient(ctx):
    
    color1 = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    color2 = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    gradient_image = Image.new('RGB', (1080, 1080))
    draw = ImageDraw.Draw(gradient_image)

    for y in range(1080):

        r = int(color1[0] + (color2[0] - color1[0]) * y / 1080)
        g = int(color1[1] + (color2[1] - color1[1]) * y / 1080)
        b = int(color1[2] + (color2[2] - color1[2]) * y / 1080)
        draw.line([(0, y), (1080, y)], fill=(r, g, b))

    gradient_image_bytesio = io.BytesIO()
    gradient_image.save(gradient_image_bytesio, format='PNG')
    gradient_image_bytesio.seek(0)

    await ctx.reply(file=discord.File(gradient_image_bytesio, 'gradient.png'))

#---------------------------------------------------------#
#                  :ON_Message commands:                  #
#---------------------------------------------------------#

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
#1- Bubble Call
    
    if message.content.lower() == "bubble":
        await message.channel.send("GUH!!!!", reference=message)
        
#2- Poke
    
    if message.content.lower() == "poke":
        file = open("miscellaneous/poke.txt", "r")
        content = file.read()
        all_lines = content.splitlines( )
        output = random.choice(all_lines) 
        await message.channel.send(output, reference=message)
        
#3- Mentions
    
    if message.content.lower() == "<@1131529056882524212>":
        await message.channel.send("RAAAAAAAAAH!!!!", reference=message)
        
#4- Reply
    
    if message.reference:
        replied_message = message.reference.resolved
        if replied_message.author == bot.user:
            await message.channel.trigger_typing()
            await message.reply("murr :3")
    
    await bot.process_commands(message)

#---------------------------------------------------------#
#                    :Slash Commands:                     #
#---------------------------------------------------------#

#1- Help

@bot.slash_command(name="help", description="BubbleBot's information")
async def help_slash(ctx):
    embed = discord.Embed(
        title="BubbleBot Help",
        description="Here's a list of available commands:",
        color=discord.Color(0x9FC6F6)
    )
    
    thumbnail_url = "https://cdn.discordapp.com/attachments/1142411437688500274/1146230560205840446/output-onlinegiftools_2.gif"
    embed.set_thumbnail(url=thumbnail_url)
    
    embed.add_field(name="__**/cta**__", value="**╰→** sends a random picture of a cat", inline=True)
    embed.add_field(name="__**/draw**__", value="**╰→** sends a randomly generated pic", inline=True)
    embed.add_field(name="__**/number_guess**__", value="**╰→** guess the number within 15 seconds, type **cancel** to cancel the game", inline=True)
    embed.add_field(name="__**/not_sfw**__", value="**╰→** sends a **totally family friendly** picture based on a tag (bomb will send 5 pictures)", inline=True)
    embed.add_field(name="__**/sfw**__", value="**╰→** sends a Random **safe anmie** picture (bomb will send 5 pictures)", inline=True)
    embed.add_field(name="__**BB Search**__", value="**╰→** search for pictures using google images", inline=True)
    embed.add_field(name="__**BB Google**__", value="**╰→** same as **bb search** but higher quality (limited to 100 per day)", inline=True)
    embed.add_field(name="__**BB Moise**__", value="**╰→** sends Pictures of moise", inline=True)
    embed.add_field(name="__**BB Pfp**__", value="**╰→** sends users' profile pictures", inline=True)
    embed.add_field(name="__**BB Pet**__", value="**╰→** pet a user or a server emoji", inline=True)

    embed.set_footer(text="Feel free to reach out if you encounter any problems or have something to share by using (BB Contact)")
    
    await ctx.respond(embed=embed)

#2- Number Guessing

game_in_progress = False

@bot.slash_command(name="number_guess", description="Guess the randomly generated number!")
async def guess_the_number(ctx):
    global game_in_progress

    if game_in_progress:
        await ctx.respond("A game is already in progress. Please wait for it to finish.")
        return

    game_in_progress = True
    await ctx.respond("Guess a number between 1-100")

    random_number = random.randint(1, 100)
    num_guesses = 0

    def check_guess(message):
        return message.author == ctx.author and (message.content.lower() == "cancel" or message.content.isdigit())

    try:
        while True:
            guess = await bot.wait_for("message", timeout=30, check=check_guess)

            if guess.content.lower() == "cancel":
                await ctx.send(f"{ctx.author.mention} has canceled the game. The correct number was {random_number}.", reference=guess)
                break

            num_guesses += 1
            user_guess = int(guess.content)

            if user_guess == random_number:
                await ctx.send(f"Congratulations, {ctx.author.mention}! You guessed the number {random_number} in {num_guesses} guesses.", reference=guess)
                break
            elif user_guess < random_number:
                await ctx.send("Higher! Guess again.", reference=guess)
            else:
                await ctx.send("Lower! Guess again.", reference=guess)

    except asyncio.TimeoutError:
        await ctx.send(f"Time's up! The correct number was {random_number}.")

    game_in_progress = False
    
#3- Draw Command

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
                  
#4-cta posting command

@bot.slash_command(name="cta", description="Send a random cta picture")
async def random_cat(ctx):
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.thecatapi.com/v1/images/search")
        if response.status_code == 200:
            data = response.json()
            cta_url = data[0]["url"]
            await ctx.respond(content=cta_url)
        else:
            await ctx.send("Failed to find cta :(")
            
#5- waifu-nsfw

def load_sent_image_urls():
    if os.path.exists("sent_image_urls.json"):
        with open("sent_image_urls.json", "r") as file:
            return set(json.load(file))
    return set()

@bot.slash_command(name="not_sfw", description="WARNING this command is NOT sfw")
async def get_picture(ctx, tag: str, bomb: bool = False):
    
    tag = tag.replace(" ", "_").replace("boob", "boobs").replace("oppai", "boobs").lower()
    
    if not ctx.channel.is_nsfw():
        await ctx.respond("This Channel is Not Hun'in 🤠.")
        return

    max_pages = 440
    
    for _ in range(max_pages):
        random_page = random.randint(1, 440)
        
        tag = " " + tag.lower()
        
        url = f"https://konachan.com/post.json?tags={tag}&limit=0&page={random_page}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                sent_image_urls = load_sent_image_urls()
                
                new_data = [item for item in data if item['file_url'] not in sent_image_urls and "loli" not in item.get('tags', '').lower()]
                
                if new_data:
                    num_images = 5 if bomb else 1
                    chosen_data = random.sample(new_data, num_images)
                    image_urls = [item['file_url'] for item in chosen_data]
                    
                    if bomb:
                        await ctx.respond(f"{ctx.author.mention} just dropped **{tag}**  bomb")
                    
                    for image_url in image_urls:
                        if bomb:
                            await ctx.respond(image_url)
                        else:
                            embed = discord.Embed(title=f"Your tag was: {tag}", colour=discord.Colour(0x9FC6F6))
                            embed.set_image(url=image_url)
                            await ctx.respond(embed=embed)
                        
                        sent_image_urls.add(image_url)
                    
                    with open("sent_image_urls.json", "w") as file:
                        json.dump(list(sent_image_urls), file)
                else:
                    await ctx.respond("No new images found for the provided tags.")
            else:
                await ctx.respond("No images found for the provided tags.")
                
            break
        else:
            await ctx.respond("Failed to fetch image from the API.")

#6- waifu sfw

def load_sent_image_urls_safe():
    filename = "sent_image_urls_safe.json"
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return set(json.load(file))
    return set()

@bot.slash_command(name="sfw", description="Get a Safe Anmie Pictures")
async def get_pictures_safe(ctx, bomb: bool = False):
    max_pages = 440
    
    for _ in range(max_pages):
        random_page = random.randint(1, 440)
        
        url = f"https://konachan.com/post.json?tags=rating:safe&limit=0&page={random_page}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                filename = "sent_image_urls_safe.json"
                sent_image_urls = load_sent_image_urls()
                
                new_data = [item for item in data if item['file_url'] not in sent_image_urls and "loli" not in item.get('tags', '').lower()]
                
                if new_data:
                    num_images = 5 if bomb else 1
                    chosen_data = random.sample(new_data, num_images)
                    image_urls = [item['file_url'] for item in chosen_data]
                    
                    if bomb:
                        await ctx.respond(f"{ctx.author.mention} just dropped a waifu bomb")
                    
                    for image_url in image_urls:
                        if bomb:
                            await ctx.send(image_url)
                        else:
                            embed = discord.Embed(title="Here's a Random Waifu Picture", colour=discord.Colour(0x9FC6F6))
                            embed.set_image(url=image_url)
                            await ctx.respond(embed=embed)
                        
                        sent_image_urls.add(image_url)
                    
                    with open(filename, "w") as file:
                        json.dump(list(sent_image_urls), file)
                    
                else:
                    await ctx.send("No new images found.")
            else:
                await ctx.send("No images found.")
                
            break
        else:
            await ctx.send("Failed to fetch image from the API.")

#7- ScreenShot haku

@bot.slash_command(name="screenshot", description="take screenshots of urls")
async def ss(ctx, url:str = None):
  if not url:
    await ctx.respond("pls give a link")
    return 0
  else:
    link = f"{url}"
    os.system(f'firefox -screenshot {link}')
    embed = discord.Embed(title="Firefox:", description=f"*{link}*", color=0x8E6539)
    file = discord.File("screenshot.png", filename="image.png")
    embed.set_image(url="attachment://image.png")
    await ctx.respond(file=file, embed=embed)
    os.remove("screenshot.png")
            

#---------------------------------------------------------#
#              always on (thx to Haku), token             #
#---------------------------------------------------------#

#Status Changer

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    change_status.start()

    channel_id = 1142387860650082334
    channel = bot.get_channel(channel_id)

    if channel:

        embed = discord.Embed(
            title="READY!",
            description="Bubble is online!",
            color=0x9FC6F6
        )

        await channel.send(embed=embed)


@tasks.loop(seconds=5)
async def change_status():
  await bot.change_presence(activity=discord.Game(random.choice(["/help | bb help", "hey don't do that ?¿"])))

#error log

@bot.event
async def on_command_error(ctx, error):
    channel_id = 1142387860650082334

    embed = discord.Embed(
        title=f'Command Error in {ctx.command}',
        description=str(error),
        color=discord.Color(int("0x9FC6F6", 16)))

    current_time = datetime.datetime.now()
    embed.set_footer(text=current_time.strftime("%Y-%m-%d %H:%M:%S"))

    await bot.get_channel(channel_id).send(embed=embed)

bot.run(os.environ['TOKEN'])