import discord
import os
import random

from discord.ext import commands


#prefixes


prefixes = ["bb ", "bB ", "BB ", "Bb "]

bot = commands.Bot(command_prefix=prefixes, intents=discord.Intents.all())

#prefix commands


bot.load_extension("commands.prefix.test")

bot.load_extension("commands.prefix.google_images")

bot.load_extension("commands.prefix.google_images_low")

#slash commands


bot.load_extension('commands.slash.draw_noise')

bot.load_extension('commands.slash.rcat')

bot.load_extension('commands.slash.pfp')

bot.load_extension('commands.slash.pet')

bot.load_extension('commands.slash.r36')

bot.load_extension('commands.slash.sfw')

bot.load_extension('commands.slash.not_sfw')

bot.load_extension('commands.slash.help')

bot.load_extension('commands.slash.contact')

#ETC

POKE_FILE_PATH = "miscellaneous/text files/poke.txt"
MENTIONED_USER_ID = "<@1131529056882524212>"
ERROR_CHANNEL_ID = 1142387860650082334


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
    await bubble_call(message)
    await poke(message)
    await mentions(message)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Bubble is in {len(bot.guilds)} servers")
    await bot.change_presence(activity=discord.Game("/help | bb help"))

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