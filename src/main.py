import discord
import os

from discord.ext import commands

from on_message import bubble_call, poke, mentions


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

#on_message


@bot.event
async def on_message(message):
    await bubble_call(message)
    await poke(message)
    await mentions(message)
    await bot.process_commands(message)

#TOEKN


bot.remove_command("help")

bot.run(os.environ['TOKEN'])