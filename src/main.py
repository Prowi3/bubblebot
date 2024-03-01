import discord
import os
import random
from discord.ext import commands

#prefixes

prefixes = ["bb ", "bB ", "BB ", "Bb "]
bot = commands.Bot(command_prefix=prefixes, intents=discord.Intents.all())

# Prefix commands

prefix_commands = [
    "commands.prefix.test",
    "commands.prefix.google_images",
    "commands.prefix.google_images_low"
]

for command in prefix_commands:
    bot.load_extension(command)

# Slash commands

slash_commands = [
    'commands.slash.draw_noise',
    'commands.slash.rcat',
    'commands.slash.pfp',
    'commands.slash.pet',
    'commands.slash.r36',
    'commands.slash.sfw',
    'commands.slash.not_sfw',
    'commands.slash.help',
    'commands.slash.contact'
]

for command in slash_commands:
    bot.load_extension(command)


# ETC

POKE_FILE_PATH = "miscellaneous/text files/poke.txt"
MENTIONED_USER_ID = "<@1131529056882524212>"
ERROR_CHANNEL_ID = 1142387860650082334
READY_CHANNEL_ID = 1213257302455615518

async def bubble_call(message):
    if message.author.bot or not message.content.lower().startswith("bubble"):
        return
    await message.channel.send("GUH!!!!", reference=message)

async def poke(message):
    if message.author.bot or not message.content.lower().startswith("poke"):
        return
    try:
        with open(POKE_FILE_PATH, "r") as file:
            output = random.choice(file.readlines())
        await message.channel.send(output, reference=message)
    except FileNotFoundError:
        await message.channel.send("Error: Poke file not found.", reference=message)
    except Exception as e:
        await message.channel.send(f"An error occurred: {e}", reference=message)

async def mentions(message):
    if message.author.bot or MENTIONED_USER_ID not in message.content.lower():
        return
    await message.channel.send("RAAAAAAAAAH!!!!", reference=message)

@bot.event
async def on_message(message):
    await bot.process_commands(message)  # This line is important for processing commands
    await bubble_call(message)
    await poke(message)
    await mentions(message)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Bubble is in {len(bot.guilds)} servers")
    await bot.change_presence(activity=discord.Game("poker | /help"))
    
    channel = bot.get_channel(READY_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="READY", color=discord.Color.white())
        await channel.send(embed=embed)
    else:
        print("Channel not found.")

@bot.event
async def on_command_error(ctx, error):
    embed = discord.Embed(
        title=f"Command Error in {ctx.command}",
        description=str(error),
        color=discord.Color(int("0x9FC6F6", 16))
    )
    channel = bot.get_channel(ERROR_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)
    else:
        print(f"Channel with ID {ERROR_CHANNEL_ID} not found.")
    await ctx.send(embed=embed)

#TOEKN

bot.remove_command("help")
bot.run(os.environ['TOKEN'])

