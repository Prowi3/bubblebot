import discord
from discord.ext import commands
import os
import requests
import base64

class Imagine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_token = os.getenv("IMAGINE")
        self.api_url = "https://api-inference.huggingface.co/models/dalle-mini/dalle-mini/mega-1-fp16:latest"

    @commands.slash_command(name="imagine", description="Generate an image from a prompt")
    async def imagine(self, ctx, *, prompt: str):
        await ctx.defer()

        headers = {
            "Authorization": f"Bearer {self.api_token}"
        }
        data = {
            "inputs": prompt
        }

        response = requests.post(self.api_url, headers=headers, json=data)

        if response.status_code != 200:
            await ctx.respond(f"Failed to generate image: {response.status_code} {response.text}", ephemeral=True)
            return

        result = response.json()

        images = result.get("images")
        if not images:
            await ctx.respond("No images returned from the API.", ephemeral=True)
            return

        img_b64 = images[0].split(",")[-1]
        img_data = base64.b64decode(img_b64)

        img_path = f"/tmp/{ctx.author.id}_imagine.png"
        with open(img_path, "wb") as f:
            f.write(img_data)

        file = discord.File(img_path, filename="image.png")
        embed = discord.Embed(description="Here's your image")
        embed.set_image(url="attachment://image.png")

        await ctx.respond(embed=embed, file=file)

        try:
            os.remove(img_path)
        except Exception:
            pass

def setup(bot):
    bot.add_cog(Imagine(bot))