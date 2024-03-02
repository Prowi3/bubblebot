import discord
from discord.ext import commands

class Contact(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_channel_id = 1147741557001289839

    @commands.slash_command(name="contact", description="Send us a message :)")
    async def contacting(self, ctx, *, message):
        target_channel = self.bot.get_channel(self.target_channel_id)
        
        formatted_message = f'{ctx.author.mention} says: "{message}"'

        await target_channel.send(formatted_message)

        await ctx.respond("Your message has been successfully sent!", ephemeral=True)

def setup(bot):
    bot.add_cog(Contact(bot))
