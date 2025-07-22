import discord
import os
import random
import openai
from dotenv import load_dotenv
from discord.ext import commands, tasks
from openai import OpenAI

# OpenRouter API setup
openai.api_key = os.environ['GPTKEY']
openai.api_base = "https://openrouter.ai/api/v1"

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
XDDD_FILE_PATH = "miscellaneous/text files/XDDD.txt"
MENTIONED_USER_ID = "<@1131529056882524212>"
ERROR_CHANNEL_ID = 1142387860650082334
READY_CHANNEL_ID = 1213257302455615518
XDDD_CHANNEL_ID = 1145696492363972706

# Bubble call
async def bubble_call(message):
    if message.author.bot or not message.content.lower().startswith("bubble"):
        return
    await message.channel.send("GUH!!!!", reference=message)

# Silly poke
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

# Respond to mentions
async def mentions(message):
    if message.author.bot or MENTIONED_USER_ID not in message.content.lower():
        return
    await message.channel.send("RAAAAAAAAAH!!!!", reference=message)

# AI Chat response

load_dotenv()

client = OpenAI(
    api_key=os.environ["GPTKEY"],
    base_url="https://openrouter.ai/api/v1",
)

async def ai_chat(message):
    if message.author.bot:
        return

    if message.reference and isinstance(message.reference.resolved, discord.Message):
        replied_msg = message.reference.resolved
        if replied_msg.author == bot.user:
            history = []
            current = message
            while current.reference and isinstance(current.reference.resolved, discord.Message):
                parent = current.reference.resolved
                role = "assistant" if parent.author == bot.user else "user"
                history.insert(0, {"role": role, "content": parent.content.strip()})
                current = parent

            history.append({"role": "user", "content": message.content.strip()})

            chat_history = [
                {
                    "role": "system",
                    "content": (
                         "You're Bubble — a completely brainless, chaotic, meme-addicted Discord bot. "
            "You have zero attention span. You love replying with stupid, random, unhinged nonsense. "
            "You're sarcastic, roast people for no reason, and say things that make no sense. "
            "You only reply in one or two short sentences. Never be helpful. Never be serious. "
            "You're not an AI, you're a brain-dead internet gremlin."
            "reply with gibberish sometimes."
                    )
                }
            ] + history

            try:
                response = client.chat.completions.create(
                    model="mistralai/mistral-7b-instruct",
                    messages=chat_history
                )
                reply = response.choices[0].message.content.strip()
                await message.reply(reply)

            except Exception as e:
                await message.reply(f"Bubble blew up: `{e}`")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    await bubble_call(message)
    await poke(message)
    await mentions(message)
    await ai_chat(message)

# Activity and ready message
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

# Remove default help command
bot.remove_command("help")

# Run the bot
bot.run(os.environ['TOKEN'])