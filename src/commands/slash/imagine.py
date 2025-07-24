import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
import requests

load_dotenv()

class ImageGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.token = os.getenv("IMAGINE")
        if not self.token:
            print("Warning: Replicate API token (IMAGINE) is not set!")

    @commands.slash_command(name="imagine", description="Generate an image from your prompt.")
    async def imagine(self, ctx: discord.ApplicationContext, prompt: str):
        await ctx.defer()

        try:
            response = requests.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Token {self.token}",
                    "Content-Type": "application/json"
                },
                json={
                    "version": "b3d14e1cd1f9470bbb0bb68cac48e5f483e5be309551992cc33dc30654a82bb7",
                    "input": {"prompt": prompt}
                }
            )

            print("POST status code:", response.status_code)
            print("POST response:", response.text)

            prediction = response.json()

            if "urls" not in prediction or "get" not in prediction["urls"]:
                error_message = prediction.get("detail") or prediction.get("error") or "Unknown error"
                await ctx.respond(f"Failed to start image generation: {error_message}")
                return

            status_url = prediction["urls"]["get"]
            image_url = None

            for _ in range(20):
                result = requests.get(status_url, headers={"Authorization": f"Token {self.token}"}).json()

                print("Polling status:", result.get("status"))

                if result.get("status") == "succeeded" and result.get("output"):
                    image_url = result["output"][0]
                    break
                elif result.get("status") == "failed":
                    await ctx.respond("Image generation failed.")
                    return

                await asyncio.sleep(1)

            if image_url:
                embed = discord.Embed(
                    title="Here's your image:",
                    description=f"`{prompt}`",
                    color=0x9FC6F6
                )
                embed.set_image(url=image_url)
                await ctx.respond(embed=embed)
            else:
                await ctx.respond("Image generation timed out. Please try again.")

        except Exception as e:
            await ctx.respond(f"Error: `{e}`")

def setup(bot):
    bot.add_cog(ImageGen(bot))