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

bot.load_extension('commands.slash.r36')

bot.load_extension('commands.slash.sfw')

bot.load_extension('commands.slash.not_sfw')

bot.load_extension('commands.slash.help')

bot.load_extension('commands.slash.contact')

#TOEKN


bot.remove_command("help")

bot.run(os.environ['TOKEN'])