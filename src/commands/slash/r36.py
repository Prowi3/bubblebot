import discord
from discord.ext import commands
import requests
import xml.etree.ElementTree as ET
import random

class R34(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sent_urls = set()

    @commands.slash_command(name="r36", description="Get random images or videos from R34")
    async def r36(self, ctx, tag: str):
        if not ctx.channel.is_nsfw():
            await ctx.respond("This command can only be used in NSFW channels.", ephemeral=True)
            return
        
        await ctx.defer()

        tag = tag.replace(" ", "_").lower()

        url = f"https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&tags={tag}"
        response = requests.get(url)

        if response.status_code == 200 and response.content:
            data = response.text

            root = ET.fromstring(data)

            posts = root.findall('.//post')

            if posts:
                new_posts = [post for post in posts if post.get('file_url') not in self.sent_urls]

                if not new_posts:
                    await ctx.respond("All available images for this tag have already been sent.", ephemeral=True)
                    return

                random_post = random.choice(new_posts)
                file_url = random_post.get('file_url')

                self.sent_urls.add(file_url)

                if file_url.endswith(".mp4"):
                    await ctx.respond(f"[You searched for {tag}. Here's a video:]({file_url})")
                else:
                    embed = discord.Embed(
                        title=f"You searched for {tag}.",
                        color=discord.Colour(0x9FC6F6)
                    )
                    embed.set_image(url=file_url)

                    await ctx.respond(embed=embed)
            else:
                await ctx.respond(f"No images found for the provided tag ({tag}).", ephemeral=True)
        else:
            await ctx.respond(f"Error fetching images. Status code: {response.status_code}", ephemeral=True)

def setup(bot):
    bot.add_cog(R34(bot))