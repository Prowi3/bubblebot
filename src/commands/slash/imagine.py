import discord
from discord.ext import commands
import os
import requests
import io
from dotenv import load_dotenv

load_dotenv()

class ImageGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hf_token = os.getenv("IMAGINE")
        if not self.hf_token:
            print("Warning: Hugging Face API token (IMAGINE) not set!")

    @commands.slash_command(name="imagine", description="Generate an image from your prompt using Stable Diffusion 2.1.")
    async def imagine(self, ctx: discord.ApplicationContext, prompt: str):
        await ctx.defer()

        try:
            API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            payload = {
                "inputs": prompt,
                "options": {"wait_for_model": True}
            }

            response = requests.post(API_URL, headers=headers, json=payload)
            print("Status:", response.status_code, response.headers.get("content-type"))
            print("Response snippet:", response.text[:200])

            if response.status_code != 200:
                await ctx.respond(f"Error from API: {response.status_code} {response.text}")
                return

            if response.headers.get("content-type", "").startswith("application/json"):
                error = response.json().get("error", "Unknown error")
                await ctx.respond(f"API error: {error}")
                return

            image_data = response.content
            image_file = discord.File(io.BytesIO(image_data), filename="image.png")

            embed = discord.Embed(
                title="Here's your image:",
                description=f"`{prompt}`",
                color=0x9FC6F6
            )
            embed.set_image(url="attachment://image.png")
            await ctx.respond(embed=embed, file=image_file)

        except Exception as e:
            await ctx.respond(f"Exception: `{e}`")

def setup(bot):
    bot.add_cog(ImageGen(bot))