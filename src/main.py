import discord
import os
import random
from discord.ext import commands

# Prefixes

prefixes = ["bb ", "bB ", "BB ", "Bb "]
bot = commands.Bot(command_prefix=prefixes, intents=discord.Intents.all())

# Load Commands

prefix_commands = [
    "commands.prefix.test",
    "commands.prefix.google_images",
    "commands.prefix.google_images_low",
    "commands.prefix.status"
]

for command in prefix_commands:
    bot.load_extension(command)

commands_directory = os.path.join('src', 'commands', 'slash')

command_files = [file[:-3] for file in os.listdir(commands_directory) if file.endswith('.py')]

for file in command_files:
    try:
        module_path = f'commands.slash.{file}'
        bot.load_extension(module_path)
        print(f"Loaded extension: {module_path}")
    except Exception as e:
        print(f"Failed to load extension {module_path}: {e}")


# Variables

POKE_FILE_PATH = "miscellaneous/text files/poke.txt"
MENTIONED_USER_ID = "<@1131529056882524212>"
ERROR_CHANNEL_ID = 1142387860650082334
READY_CHANNEL_ID = 1213257302455615518

# Bubble call

async def bubble_call(message):
    if message.author.bot or not message.content.lower().startswith("bubble"):
        return
    await message.channel.send("GUH!!!!", reference=message)

# silly poke

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

# respond to mentions

async def mentions(message):
    if message.author.bot or MENTIONED_USER_ID not in message.content.lower():
        return
    await message.channel.send("RAAAAAAAAAH!!!!", reference=message)

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    await bubble_call(message)
    await poke(message)
    await mentions(message)

# activity, ready message

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game("poker | /help"))
    
    channel = bot.get_channel(READY_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="READY",
            description=str(f"{bot.user} is Ready and in {len(bot.guilds)} servers"),
            color=discord.Color(int("0x9FC6F6", 16))
        )
        await channel.send(embed=embed)
    else:
        print("Channel not found.")

# Error handling

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

# TOEKN and Remove default commands

bot.remove_command("help")
bot.run(os.environ['TOKEN'])