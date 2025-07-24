import discord
from discord.ext import commands
import httpx

class ImageGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="imagine", description="Generate an AI image from your prompt")
    async def imagine(self, ctx: discord.ApplicationContext, prompt: str):
        await ctx.defer()
        url = f"https://lexica.art/api/v1/search?q={prompt}"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
            images = data.get("images")
            if not images:
                await ctx.respond("No images found for your prompt.")
                return
            image_url = images[0]["srcLarge"] or images[0]["srcSmall"]
            embed = discord.Embed(
                title="Here’s your AI-generated image!",
                description=f"`{prompt}`",
                color=0x00B2FF
            )
            embed.set_image(url=image_url)
            await ctx.respond(embed=embed)
        except Exception as e:
            await ctx.respond(f"Failed to generate image: {e}")

def setup(bot):
    bot.add_cog(ImageGen(bot))