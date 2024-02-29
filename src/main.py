import discord
import random
import os
import httpx
import asyncio
import requests
import json
import urllib.parse
import aiohttp
import datetime
import math
import numpy as np
import noise
import re
import xml.etree.ElementTree as ET


from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
from bs4 import BeautifulSoup
from io import BytesIO
from petpetgif import petpet as petpetgif
from googleapiclient.discovery import build

#prefixes and unimportant shit

prefixes = ["bb ", "bB ", "BB ", "Bb "]

bot = commands.Bot(command_prefix=prefixes, intents=discord.Intents.all())

bot.load_extension("commands.test")

bot.remove_command("test")

#-------------------------------------------------------#
#                    :prefix commands:                  #
#-------------------------------------------------------#

# BB hello/Contact/say/stinky

@bot.command()
async def hello(ctx):
    await ctx.send("https://media.discordapp.net/attachments/1065649826341072999/1126008651392483509/AutoMemes.gif", reference=ctx.message)

@bot.command()
async def stinky(ctx):
    await ctx.send("https://cdn.discordapp.com/attachments/1142411437688500274/1194295787161665647/20231018_020109.jpg?ex=65afd5a0&is=659d60a0&hm=47e144741c29b716e637bbd92af279cdfd40501bda3a253eb5b5e41b266b9f44&", reference=ctx.message)

CHANNEL_ID = 1147741557001289839

@bot.slash_command(name="contact", description="send me a message :)")
async def contacting(ctx, *, message):
    target_channel = bot.get_channel(CHANNEL_ID)
    
    formatted_message = f'{ctx.author.mention} says: "{message}"'

    await target_channel.send(formatted_message)

    await ctx.respond("Your message has been successfully sent!", ephemeral=True)

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

#1- BB Search

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

#2- BB Google

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

#Help

class PrevButton(discord.ui.Button):
    def __init__(self, paginate):
        super().__init__(style=discord.ButtonStyle.secondary, label="Previous", custom_id="prev_button")
        self.paginate = paginate

    async def callback(self, interaction):
        self.paginate.current_page = max(0, self.paginate.current_page - 1)
        
        if self.paginate.current_page < 2:
            self.paginate.next_button.style = discord.ButtonStyle.success
        
        await self.paginate.update_page(self.paginate.current_page, interaction.message)
        await interaction.response.defer()

class NextButton(discord.ui.Button):
    def __init__(self, paginate):
        super().__init__(style=discord.ButtonStyle.success, label="Next", custom_id="next_button")
        self.paginate = paginate

    async def callback(self, interaction):
        self.paginate.current_page = min(len(self.paginate.pages) - 1, self.paginate.current_page + 1)
        
        if self.paginate.current_page == 2:
            self.style = discord.ButtonStyle.danger
        else:
            self.style = discord.ButtonStyle.success
        
        await self.paginate.update_page(self.paginate.current_page, interaction.message)
        await interaction.response.defer()

class Paginate:
    def __init__(self, ctx):
        self.pages = ["", "", ""]
        self.current_page = 0
        self.ctx = ctx
        self.prev_button = PrevButton(self)
        self.next_button = NextButton(self)
        self.view = discord.ui.View()
        self.view.add_item(self.prev_button)
        self.view.add_item(self.next_button)

    async def update_page(self, page, message):
        page_dict = eval(self.pages[page])
        embed = discord.Embed.from_dict(page_dict)
        await message.edit(embed=embed, view=self.view)

@bot.command()
async def help(ctx):
    p = Paginate(ctx)

    # Page 1
    embed1 = discord.Embed(
        title="BubbleBot Help",
        description="Here's a list of available commands:",
        color=discord.Color(0x9FC6F6)
    )
    thumbnail_url = "https://cdn.discordapp.com/attachments/1142411437688500274/1146230560205840446/output-onlinegiftools_2.gif"
    embed1.set_thumbnail(url=thumbnail_url)

    embed1.add_field(name="__**/cta**__", value="**╰→** Get a random cat picture.")
    embed1.add_field(name="__**/shapes_draw**__", value="**╰→** Generate an image with random shapes")
    embed1.add_field(name="__**/clouds_draw**__", value="**╰→** Generate an image using perlin noise")
    embed1.add_field(name="__**/pfp**__", value="**╰→** Fetch a user's profile picture.")
    embed1.add_field(name="__**/number_guess**__", value="**╰→** Guess a number within 15 seconds, type 'cancel' to stop the game.")
    embed1.add_field(name="__**/not_sfw**__", value="**╰→** Get a *totally family-friendly* picture based on a tag.")
    embed1.add_field(name="__**/sfw**__", value="**╰→** Receive a random safe anime picture.")
    embed1.add_field(name="__**/pet**__", value="**╰→** Pet users, server emotes, or image URLs.")
    embed1.add_field(name="__**/moiseinator**__", value="**╰→** Spam pictures of Moise")
    embed1.add_field(name="__**BB Search**__", value="**╰→** Search for images from Google.")
    embed1.add_field(name="__**BB Google**__", value="**╰→** High-quality image search (limited to 100 per day).")

    embed1.set_footer(text="1/3")

    p.pages[0] = str(embed1.to_dict())

    # Page 2
    embed2 = discord.Embed(
        title="/clouds_draw Help",
        description="Here's a list of what each parameter does:",
        color=discord.Color(0xFFFFFF)
    )

    thumbnail_url2 = "https://cdn.discordapp.com/attachments/1142411437688500274/1149559291313922098/New_Project_341_D93B16A.gif"
    embed2.set_thumbnail(url=thumbnail_url2)

    embed2.add_field(name="1- **Octaves**:", value="You can vary the number of octaves to control the level of detail in the noise. Higher octaves create more intricate patterns, Values around 1-10 are recommend.")
    embed2.add_field(name="2- **Lacunarity**:", value="Lacunarity affects the frequency of each successive octave. Increasing it can lead to more variations in the noise.")
    embed2.add_field(name="3- **Persistence**:", value="This parameter controls how much each successive octave contributes to the final noise. Values around 0.5 provide a balanced look, while values above 0.5 emphasize the higher octaves.")
    embed2.add_field(name="4- **Font**:", value="Select your preferred Font")
    embed2.add_field(name="5- **Text**:", value="Whatever you type will appear in the image unless it's some weird characters/emojis")

    embed2.set_footer(text="2/3")
    p.pages[1] = str(embed2.to_dict())

    # Page 3
    embed3 = discord.Embed(
        title="THAT'S BASICALLY IT!",
        description="If you encounter any issues or want to share something with us, please don't hesitate to get in touch by using (/contact). We're always here to help! :)",
        color=discord.Color(0xF23F43)
    )
    
    embed3.set_footer(text="3/3")
    
    p.pages[2] = str(embed3.to_dict())

    message = await ctx.send(embed=embed1)

    view = discord.ui.View()
    view.add_item(PrevButton(p))
    view.add_item(NextButton(p))

    await message.edit(view=view)

#-------------------------------------------------------#
#                :ON_Message commands:                  #
#-------------------------------------------------------#

PREFIXES = (
    "<3 ",
    "0w0 ",
    "H-hewwo ",
    "HIIII! ",
    "Haiiii! ",
    "Huohhhh. ",
    "OWO ",
    "OwO ",
    "UwU ",
    "murr :3 ",
    ">_< ",
    "*blush* ",
    "*waises paw* "
)

SUFFIXES = (
    " ( ˘ ³˘)",
    " (´・ω・｀)",
    " (OωO! )",
    " (๑•́ ₃ •̀๑)",
    " (• o •)",
    " (╯﹏╰）",
    " (●´ω｀●)",
    " (◠‿◠✿)",
    " (✿ ♡‿♡)",
    " (人◕ω◕)",
    " (；ω；)",
    " ._.",
    " :3",
    " :D",
    " :P",
    " ;-;",
    " ;3",
    " >:3"
    " (⁠≧⁠▽⁠≦⁠)",
    " >_<",
    " UwU",
    " XDDD",
    " \\°○°/",
    " ^-^",
    " ^_^",
    " x3",
    " xD",
    " ÙωÙ",
    " ㅇㅅㅇ",
    ", fwendo",
    "（＾ｖ＾）",
    " nuzzles u",
    " x3c",
    " nya~"
)

SUBSTITUTIONS = {
    "love": "wuv",
    "Love": "Wuv",
    "loving": "wuving",
    "Loving": "Wuving",
    "mr ": "mistuh",
    "Mr ": "Mistuh",
    "r": "w",
    "l": "w",
    "R": "W",
    "L": "W",
    "th ": "f ",
    "no": "nu",
    "No": "Nu",
    "has": "haz",
    "Has": "Haz",
    "have": "haz",
    "Have": "Haz",
    "says": "sez",
    "Says": "Sez",
    "you": "uu",
    "i've": "i",
    "I've": "I",
    "the ": "da ",
    "The ": "Da ",
    "qu": "qw",
    "Qu": "Qw",
    "pause ": "paws ",
    "Pause ": "Paws ",
    "paus": "paws",
    "Paus": "Paws",
    "stfu": "RUDE!",
    "STFU": "(⁠•⁠ ⁠▽⁠ ⁠•⁠;⁠)",
    "Stfu": "(⁠;⁠ŏ⁠﹏⁠ŏ⁠)",
    "Fuck": "Fwick",
    "fuck": "fwick",
    "hell": "heck",
    "FUCK": "FWICK!"
}

def add_affixes(input_string, prefixes=PREFIXES, suffixes=SUFFIXES):
    if not isinstance(input_string, str):
        raise TypeError("input_string must be a string")
    if not isinstance(prefixes, (list, tuple)):
        raise TypeError("Prefixes must be passed as a list or tuple")
    if not isinstance(suffixes, (list, tuple)):
        raise TypeError("Suffixes must be passed as a list or tuple")

    stutters = ['u', 'w']

    if random.random() < 0.1:
        input_string = ''.join([random.choice(stutters) + c for c in input_string])

    if input_string and random.random() < 0.5:
        input_string = input_string[0] + '-' + input_string

    return random.choice(prefixes) + input_string + random.choice(suffixes)

def substitute(input_string, substitutions=None):
    if not isinstance(input_string, str):
        raise TypeError("input_string must be a string")
    if substitutions is None:
        substitutions = SUBSTITUTIONS
    if not isinstance(substitutions, dict):
        raise TypeError("Substitutions must be passed as a dictionary")
    for sub in substitutions:
        input_string = input_string.replace(sub, substitutions[sub])
    return input_string

def owo(input_string, substitutions=None, prefixes=PREFIXES, suffixes=SUFFIXES):
    return add_affixes(substitute(input_string, substitutions=substitutions), prefixes=prefixes, suffixes=suffixes)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
        
#1- Bubble Call
    
    if message.content.lower() == "bubble":
        await message.channel.send("GUH!!!!", reference=message)
        
#2- Poke
    
    if message.content.lower() == "poke":
        file = open("miscellaneous/text files/poke.txt", "r")
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
            await message.reply(owo(message.content))
    
    await bot.process_commands(message)

#-------------------------------------------------------#
#                  :Slash Commands:                     #
#-------------------------------------------------------#

#1- Help

@bot.slash_command(name="help", description="BubbleBot's information")
async def help_slash(ctx):
    p = Paginate(ctx)

    # Page 1
    embed1 = discord.Embed(
        title="BubbleBot Help",
        description="Here's a list of available commands:",
        color=discord.Color(0x9FC6F6)
    )
    thumbnail_url = "https://cdn.discordapp.com/attachments/1142411437688500274/1146230560205840446/output-onlinegiftools_2.gif"
    embed1.set_thumbnail(url=thumbnail_url)

    embed1.add_field(name="__**/cta**__", value="**╰→** Get a random cat picture.")
    embed1.add_field(name="__**/shapes_draw**__", value="**╰→** Generate an image with random shapes")
    embed1.add_field(name="__**/clouds_draw**__", value="**╰→** Generate an image using perlin noise")
    embed1.add_field(name="__**/pfp**__", value="**╰→** Fetch a user's profile picture.")
    embed1.add_field(name="__**/number_guess**__", value="**╰→** Guess a number within 15 seconds, type 'cancel' to stop the game.")
    embed1.add_field(name="__**/not_sfw**__", value="**╰→** Get a *totally family-friendly* picture based on a tag.")
    embed1.add_field(name="__**/sfw**__", value="**╰→** Receive a random safe anime picture.")
    embed1.add_field(name="__**/pet**__", value="**╰→** Pet users, server emotes, or image URLs.")
    embed1.add_field(name="__**/moiseinator**__", value="**╰→** Spam pictures of Moise")
    embed1.add_field(name="__**BB Search**__", value="**╰→** Search for images from Google.")
    embed1.add_field(name="__**BB Google**__", value="**╰→** High-quality image search (limited to 100 per day).")

    embed1.set_footer(text="1/3")

    p.pages[0] = str(embed1.to_dict())

    # Page 2
    embed2 = discord.Embed(
        title="/clouds_draw Help",
        description="Here's a list of what each parameter does:",
        color=discord.Color(0xFFFFFF)
    )

    thumbnail_url2 = "https://cdn.discordapp.com/attachments/1142411437688500274/1149559291313922098/New_Project_341_D93B16A.gif"
    embed2.set_thumbnail(url=thumbnail_url2)

    embed2.add_field(name="1- **Octaves**:", value="You can vary the number of octaves to control the level of detail in the noise. Higher octaves create more intricate patterns, Values around 1-10 are recommend.")
    embed2.add_field(name="2- **Lacunarity**:", value="Lacunarity affects the frequency of each successive octave. Increasing it can lead to more variations in the noise.")
    embed2.add_field(name="3- **Persistence**:", value="This parameter controls how much each successive octave contributes to the final noise. Values around 0.5 provide a balanced look, while values above 0.5 emphasize the higher octaves.")
    embed2.add_field(name="4- **Font**:", value="Select your preferred Font")
    embed2.add_field(name="5- **Text**:", value="Whatever you type will appear in the image unless it's some weird characters/emojis")

    embed2.set_footer(text="2/3")
    p.pages[1] = str(embed2.to_dict())

    # Page 3
    embed3 = discord.Embed(
        title="THAT'S BASICALLY IT!",
        description="If you encounter any issues or want to share something with us, please don't hesitate to get in touch by using (/contact). We're always here to help! :)",
        color=discord.Color(0xF23F43)
    )
    
    embed3.set_footer(text="3/3")
    
    p.pages[2] = str(embed3.to_dict())

    message = await ctx.respond(embed=embed1)

    view = discord.ui.View()
    view.add_item(PrevButton(p))
    view.add_item(NextButton(p))

    await message.edit_original_response(view=view)

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
                  
#3-cta posting command

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
            
#4- waifu-nsfw

@bot.slash_command(name="not_sfw", description="Fetch random NSFW image URL from yande.re")
async def get_custom_images(ctx):
    if not ctx.channel.is_nsfw():
        await ctx.respond("This is the wrong channel :]", ephemeral=True)
        return

    await ctx.defer()

    random_page = random.randint(1, 100)

    url = f"https://yande.re/post.json?tags=rating:explicit&limit=0&page={random_page}"
    response = requests.get(url)

    if response.status_code == 200 and response.content:
        data = response.json()

        if data:
            file_url = data[0]['sample_url']

            embed = discord.Embed(
                title="Random NSFW Image",
                color=discord.Color(0x9FC6F6)
            )
            embed.set_image(url=file_url)

            await ctx.respond(embed=embed)
        else:
            await ctx.respond("No images found.", ephemeral=True)
    else:
        await ctx.respond(f"Error fetching images. Status code: {response.status_code}", ephemeral=True)

#5- waifu sfw

@bot.slash_command(name="sfw", description="Fetch random SFW image URL from yande.re")
async def get_custom_images(ctx):
    await ctx.defer()

    random_page = random.randint(1, 100)

    url = f"https://yande.re/post.json?tags=rating:safe&limit=0&page={random_page}"
    response = requests.get(url)

    if response.status_code == 200 and response.content:
        data = response.json()

        if data:
            file_url = data[0]['sample_url']

            embed = discord.Embed(
                title="Random SFW Image",
                colour=discord.Colour(0x9FC6F6))
            embed.set_image(url=file_url)

            await ctx.respond(embed=embed)
        else:
            await ctx.respond("No images found.", ephemeral=True)
    else:
        await ctx.respond(f"Error fetching images. Status code: {response.status_code}", ephemeral=True)

#6- R34

@bot.slash_command(name="r36", description="Fetch images from R34")
async def get_custom_images(ctx, tag: str):
    if not ctx.channel.is_nsfw():
        await ctx.respond("This command can only be used in NSFW channels.", ephemeral=True)
        return
    
    await ctx.defer()

    tag = tag.replace(" ", "_").lower()

    url = f"https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&tags={tag}"
    response = requests.get(url)

    if response.status_code == 200 and response.content:
        data = response.text

        root = ET.fromstring(data)

        posts = root.findall('.//post')

        if posts:
            file_url = posts[0].get('file_url')

            if file_url.endswith(".mp4"):
                await ctx.respond(f"You searched for {tag}. Here's a video: {file_url}")
            else:
                embed = discord.Embed(
                    title=f"You searched for {tag}.",
                    color=discord.Colour(0x9FC6F6)
                )
                embed.set_image(url=file_url)

                await ctx.respond(embed=embed)
        else:
            await ctx.respond(f"No images found for the provided tag ({tag}).", ephemeral=True)
    else:
        await ctx.respond(f"Error fetching images. Status code: {response.status_code}", ephemeral=True)

#7- Draw_Perlin


fonts = ['Roboto-Black', 'SpaceMono-Regular', 'SpaceMono-Bold', 'DancingScript-Bold', 'Rubik-Bold', 'Arial-Black']

is_rendering = False

@bot.slash_command(name="clouds_draw", description='Draw an image using Noise, type "/help" for more ifo')
async def perlin(ctx: discord.ApplicationContext,
  font: discord.Option(str, choices=fonts) = None, *, text: str = '', octaves: int = 1, lacunarity: float = 5.0, persistence: float = 0.5):
    global is_rendering
    
    if is_rendering:
        await ctx.send("Sorry, an image is already being rendered.")
        return
    
    is_rendering = True
    
    await ctx.defer()
    
    try:
        width, height = 1080, 1080
        gradient_image = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(gradient_image)
        
        scale = 300.0
        hue_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        offset_x = random.uniform(0, 1000)
        offset_y = random.uniform(0, 1000)
        
        x_coords = np.arange(width) + offset_x
        y_coords = np.arange(height) + offset_y
        x_coords, y_coords = np.meshgrid(x_coords, y_coords)
        
        pnoise2_vectorized = np.vectorize(noise.pnoise2)
        noise_values = pnoise2_vectorized(x_coords / scale, y_coords / scale, octaves = octaves, persistence = persistence, lacunarity = lacunarity, repeatx=1024, repeaty=1024, base=1)
        
        r, g, b = hue_color
        r_values = np.clip(r + noise_values * 100, 0, 255).astype(np.uint8)
        g_values = np.clip(g + noise_values * 100, 0, 255).astype(np.uint8)
        b_values = np.clip(b + noise_values * 100, 0, 255).astype(np.uint8)
        rgb_values = np.stack([r_values, g_values, b_values], axis=-1)
        gradient_image = Image.fromarray(rgb_values)

        if text:
            draw = ImageDraw.Draw(gradient_image)
            font_size = int(math.sqrt(width * height) / len(text)) + 25
            font_path = f"miscellaneous/Fonts/{font}.ttf"
            font = ImageFont.truetype(font_path, font_size)
            text_width, text_height = draw.textsize(text, font=font)
            x = round((width - text_width) / 2) + 1
            y = round((height - text_height) / 2) + 2
            text_image = Image.new('RGB', (width, height))
            text_draw = ImageDraw.Draw(text_image)
            text_draw.text((x, y), text=text, fill=(255, 255, 255), font=font)

            gradient_image = ImageChops.soft_light(gradient_image, text_image)
            
        await ctx.respond("Here's your image.")
        gradient_image.save('gradient.png')
        await ctx.send(file=discord.File('gradient.png'))
        is_rendering = False
    
    except Exception as e:
        is_rendering = False
        await ctx.respond(f"An error occurred: {str(e)}")

#8- Get_Pfp

@bot.slash_command(name="pfp", description="Sends the Profile Picture of the User that you selected")
async def pfp(ctx, user: discord.Member = None):
    user = user or ctx.author
    pfp_url = user.avatar.url
    embed = discord.Embed(title=f"Profile Picture of {user.display_name}", color=0x9FC6F6)
    embed.set_image(url=pfp_url)
    await ctx.respond(embed=embed)

#9- Petpet

@bot.slash_command(
    name="pet",
    description="Pet Users, Server Emotes, Or Image Links")
async def pet(ctx, user: discord.Member = None, emote: str = None, image_url: str = None,):
    async with aiohttp.ClientSession() as session:
        if user:
            image_data = await user.avatar.read()
        elif emote:
            emote_match = re.match(r'<:(\w+):(\d+)>', emote)
            if emote_match:
                emote_id = int(emote_match.group(2))
                emote = discord.utils.get(ctx.guild.emojis, id=emote_id)
                if emote:
                    image_url = emote.url
                    async with session.get(image_url) as resp:
                        image_data = await resp.read()
                else:
                    await ctx.respond("Invalid petting :(")
                    return
            else:
                await ctx.respond("Invalid emote")
                return
        elif image_url:
            async with session.get(image_url) as resp:
                image_data = await resp.read()
        else:
            await ctx.respond("Please provide an image URL, mention a user, or an emote to pet.")
            return

        source = BytesIO(image_data)
        dest = BytesIO()
        petpetgif.make(source, dest)
        dest.seek(0)
        await ctx.respond(file=discord.File(dest, filename="petpet.gif"))

#-------------------------------------------------------#
#            always on (thx to Haku), token             #
#-------------------------------------------------------#

#Status Changer

@bot.event
async def on_ready():
    print(f"logged as {bot.user}")
    print(f'Bubble is in {len(bot.guilds)} servers')
    game = discord.Game("/help | bb help")
    await bot.change_presence(activity=game)

#error logs

@bot.event
async def on_command_error(ctx, error):
    channel_id = 1142387860650082334

    embed = discord.Embed(
        title=f'Command Error in {ctx.command}',
        description=str(error),
        color=discord.Color(int("0x9FC6F6", 16)))

    current_time = datetime.datetime.now()
    embed.set_footer(text=current_time.strftime("%Y-%m-%d"), icon_url="https://cdn.discordapp.com/attachments/1142411437688500274/1150989332233064468/New_Project_357_525F3E6.gif")

    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(embed=embed)
    
    await ctx.reply(embed=embed)

bot.run(os.environ['TOKEN'])