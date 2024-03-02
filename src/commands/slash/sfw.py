import discord
from discord.ext import commands
import requests
import random

class Image(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.image = discord.SlashCommandGroup("image", "Get random images from yande.re")

        @self.image.command(
            name="sfw",
            description="Get a random SFW image from yande.re"
        )
        async def sfw(self, ctx):
            await ctx.defer()

            random_page = random.randint(1, 100)

            url = f"https://yande.re/post.json?tags=rating:safe&limit=0&page={random_page}"
            response = requests.get(url)

            if response.status_code == 200 and response.content:
                data = response.json()

                if data:
                    file_url = data[0]['sample_url']

                    embed = discord.Embed(
                        title="Random SFW Image",
                        colour=discord.Colour(0x9FC6F6)
                    )
                    embed.set_image(url=file_url)

                    await ctx.respond(embed=embed)
                else:
                    await ctx.respond("No images found.", ephemeral=True)
            else:
                await ctx.respond(f"Error fetching images. Status code: {response.status_code}", ephemeral=True)

        @self.image.command(
            name="nsfw",
            description="Get a random NSFW image from yande.re"
        )
        async def nsfw(self, ctx):
            if ctx.channel.is_nsfw():
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
                            colour=discord.Colour(0xFF0000)
                        )
                        embed.set_image(url=file_url)

                        await ctx.respond(embed=embed)
                    else:
                        await ctx.respond("No images found.", ephemeral=True)
                else:
                    await ctx.respond(f"Error fetching images. Status code: {response.status_code}", ephemeral=True)
            else:
                await ctx.respond("This command can only be used in NSFW channels.", ephemeral=True)

def setup(bot):
    bot.add_cog(Image(bot))
