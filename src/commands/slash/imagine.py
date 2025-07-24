import discord
from discord.ext import commands
import os
import asyncio
import requests
from dotenv import load_dotenv

load_dotenv()

class ImageGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hf_token = os.getenv("IMAGINE")
        if not self.hf_token:
            print("Warning: Hugging Face API token (IMAGINE) not set!")

    @commands.slash_command(name="imagine", description="Generate an image from your prompt using Hugging Face Stable Diffusion.")
    async def imagine(self, ctx: discord.ApplicationContext, prompt: str):
        await ctx.defer()

        try:
            API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
            headers = {
                "Authorization": f"Bearer {self.hf_token}"
            }
            payload = {
                "inputs": prompt,
                "options": {"wait_for_model": True}
            }

            response = requests.post(API_URL, headers=headers, json=payload)

            print("Status code:", response.status_code)
            print("Response:", response.text[:300])

            if response.status_code != 200:
                await ctx.respond(f"Error from API: {response.status_code} {response.text}")
                return

            if response.headers.get("content-type", "").startswith("application/json"):
                error_json = response.json()
                error_message = error_json.get("error", "Unknown error")
                await ctx.respond(f"Error: {error_message}")
                return

            image_data = response.content
            file_path = f"/tmp/{ctx.user.id}_output.png"
            with open(file_path, "wb") as f:
                f.write(image_data)

            file = discord.File(file_path, filename="image.png")
            embed = discord.Embed(
                title="Here's your image:",
                description=f"`{prompt}`",
                color=0x9FC6F6
            )
            embed.set_image(url="attachment://image.png")
            await ctx.respond(embed=embed, file=file)

            os.remove(file_path)

        except Exception as e:
            await ctx.respond(f"Error: `{e}`")

def setup(bot):
    bot.add_cog(ImageGen(bot))