import discord
import os

from discord.ext import commands


#prefixes


prefixes = ["bb ", "bB ", "BB ", "Bb "]

bot = commands.Bot(command_prefix=prefixes, intents=discord.Intents.all())

#prefix commands


bot.load_extension("commands.prefix.test")

#slash commands

bot.load_extension('commands.slash.draw_noise')

bot.load_extension('commands.slash.rcat')

bot.load_extension('commands.slash.pfp')

bot.load_extension('commands.slash.pet')

#TOEKN


bot.remove_command("help")

bot.run(os.environ['TOKEN'])