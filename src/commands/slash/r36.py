import discord
from discord.ext import commands
import requests

sent_media_links = []

class R34(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="r36", description="Fetch images or GIFs from R34")
    async def r36(self, ctx, tag: str):
        if not ctx.channel.is_nsfw():
            await ctx.respond("This command can only be used in NSFW channels.", ephemeral=True)
            return
        
        await ctx.defer()

        tag = tag.replace(" ", "_").lower()

        url = f"https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&tags={tag}"
        response = requests.get(url)

        if response.status_code == 200 and response.content:
            data = response.json()

            media = [post['file_url'] for post in data if post['file_url'].endswith(('.jpg', '.jpeg', '.png', '.gif')) and post['file_url'] not in sent_media_links]

            if media:
                file_url = media[0]
                is_gif = file_url.endswith('.gif')
                if is_gif:
                    message = f"You searched for {tag}. Here's a GIF:"
                else:
                    message = f"You searched for {tag}. Here's an image:"

                embed = discord.Embed(
                    title=message,
                    color=0x9FC6F6
                )
                embed.set_image(url=file_url)
                await ctx.respond(embed=embed)
                sent_media_links.append(file_url)
            else:
                await ctx.respond(f"All media found for the provided tag ({tag}) have been sent or there are no media available.", ephemeral=True)
        else:
            await ctx.respond(f"Error fetching media. Status code: {response.status_code}", ephemeral=True)

def setup(bot):
    bot.add_cog(R34(bot))