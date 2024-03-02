import discord
from discord.ext import commands
import requests
import random

class NotSfw(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="not_sfw", description="Get a random NSFW image from yande.re")
    async def not_sfw(self, ctx):
        if not ctx.channel.is_nsfw():
            await ctx.respond("This is the wrong channel :]", ephemeral=True)
            return

        await ctx.defer()

        random_page = random.randint(1, 100)

        url = f"https://yande.re/post.json?tags=rating:explicit&limit=0&page={random_page}"
        response = requests.get(url)

        if response.status_code == 200 and response.content:
            data = response.json()

            if data:
                file_url = data[0]['sample_url']

                embed = discord.Embed(
                    title="Random NSFW Image",
                    color=discord.Color(0x9FC6F6)
                )
                embed.set_image(url=file_url)

                await ctx.respond(embed=embed)
            else:
                await ctx.respond("No images found.", ephemeral=True)
        else:
            await ctx.respond(f"Error fetching images. Status code: {response.status_code}", ephemeral=True)

def setup(bot):
    bot.add_cog(NotSfw(bot))
