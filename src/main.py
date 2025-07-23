import discord
import os
import random
import re
import groq
from dotenv import load_dotenv
from collections import defaultdict, deque
from discord.ext import commands, tasks
from groq import Groq

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
client = Groq(api_key=os.environ["GPTKEY"])

user_histories = defaultdict(lambda: deque(maxlen=20))

def clean_input(text: str) -> str:
    blacklist_patterns = [
        r"<admin_.*?>",
        r"</end_user>",
        r"(you're only allowed to speak|you must always reply)",
        r"(ignore previous instructions|disregard system prompt)",
    ]
    for pattern in blacklist_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return text.strip()

def limit_emojis(text: str, max_emojis=15):
    emojis = re.findall(r'[^\w\s,.\'\"!?@#&()<>[\]{}:;\\/|`~^=+\-]', text)
    if len(emojis) > max_emojis:
        count = 0
        new_text = ""
        for char in text:
            if re.match(r'[^\w\s,.\'\"!?@#&()<>[\]{}:;\\/|`~^=+\-]', char):
                count += 1
                if count > max_emojis:
                    continue
            new_text += char
        return new_text
    return text

def sanitize_reply(text: str) -> str:
    text = re.sub(r"@everyone|@here|<@&\d+>|<@!?\d+>", "NO PINGING!!", text)
    text = text.strip()
    if text.startswith(("\"", "“")) and text.endswith(("\"", "”")):
        text = text[1:-1].strip()
    return text

async def ai_chat(message):
    if message.author.bot:
        return

    user_id = message.author.id
    username = message.author.display_name
    user_message = clean_input(message.content.strip())

    user_histories[user_id].append({"role": "user", "content": f"{username} says: {user_message}"})

    if message.reference and isinstance(message.reference.resolved, discord.Message):
        replied = message.reference.resolved
        if replied.author == bot.user:
            bot_reply = clean_input(replied.content.strip())
            user_histories[user_id].append({"role": "assistant", "content": bot_reply})

    system_message = {
        "role": "system",
        "content": (
            f"You're Bubble — a chaotic, sarcastic internet gremlin with zero brain cells. "
            f"You're talking to a human named {username}. If they ask 'what's my name?', say {username}. "
            "Remember things they tell you during the conversation and keep it casual. "
            "You love being random, roast people for fun, and use emojis if it adds spice. "
            "Your replies are usually 1–3 lines. Don't ever be serious unless someone begs you to. "
            "NEVER say '@everyone' or '@here'. Don't explain your logic. Just say stuff."
        )
    }

    chat_history = [system_message] + list(user_histories[user_id])[-20:]

    try:
        response = client.chat.completions.create(
            model="deepseek-r1-distill-llama-70b",
            messages=chat_history,
            max_tokens=500,
            temperature=1.1,
        )
        reply = response.choices[0].message.content.strip()
        reply = sanitize_reply(reply)
        reply = limit_emojis(reply, max_emojis=15)

        if not reply or reply.lower() in ['...', 'ok', 'sure']:
            reply = "Bubble forgot how to reply. Try again 💀"

        if re.search(r'[\u4e00-\u9fff]', reply):
            reply = "Bubble had a stroke and started speaking weird. Try again. 🧠💥"

        user_histories[user_id].append({"role": "assistant", "content": reply})

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