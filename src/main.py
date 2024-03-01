import discord
import os

from discord.ext import commands


#prefixes


prefixes = ["bb ", "bB ", "BB ", "Bb "]

bot = commands.Bot(command_prefix=prefixes, intents=discord.Intents.all())

#prefix commands


bot.load_extension("commands.prefix.test")

#slash commands

bot.load_extension('commands.slash.clouds_draw')

bot.load_extension('commands.slash.rcat')

#TOEKN


bot.remove_command("help")

bot.run(os.environ['TOKEN'])