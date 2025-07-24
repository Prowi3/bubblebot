import discord
from discord.ext import commands
import httpx
import base64
from io import BytesIO

class ImageGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="imagine", description="Generate images using Craiyon with swipe buttons")
    async def imagine(self, ctx: discord.ApplicationContext, prompt: str):
        await ctx.defer()

        url = "https://api.craiyon.com/v3"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/113.0.0.0 Safari/537.36"
            )
        }
        data = {"prompt": prompt}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()

            json_response = response.json()
            images_b64 = json_response.get("images")
            if not images_b64:
                await ctx.respond("No images returned from the API.")
                return

            files = [
                discord.File(BytesIO(base64.b64decode(img_b64)), filename="image.png")
                for img_b64 in images_b64
            ]

            index = 0

            embed = discord.Embed(
                title=f"Image 1/{len(files)}",
                description=f"`{prompt}`",
                color=0x00B2FF
            )
            embed.set_image(url="attachment://image.png")

            class ImageView(discord.ui.View):
                def __init__(self, files):
                    super().__init__(timeout=300)
                    self.files = files
                    self.index = 0

                @discord.ui.button(label="⬅️ Prev", style=discord.ButtonStyle.secondary)
                async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
                    self.index = (self.index - 1) % len(self.files)
                    await self.update_message(interaction)

                @discord.ui.button(label="➡️ Next", style=discord.ButtonStyle.secondary)
                async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                    self.index = (self.index + 1) % len(self.files)
                    await self.update_message(interaction)

                async def update_message(self, interaction: discord.Interaction):
                    new_embed = discord.Embed(
                        title=f"Image {self.index + 1}/{len(self.files)}",
                        description=f"`{prompt}`",
                        color=0x00B2FF
                    )
                    new_embed.set_image(url="attachment://image.png")
                    await interaction.response.edit_message(
                        embed=new_embed,
                        attachments=[self.files[self.index]],
                        view=self
                    )

            view = ImageView(files)
            await ctx.respond(embed=embed, file=files[0], view=view)

        except httpx.HTTPStatusError as e:
            await ctx.respond(f"HTTP error occurred: {e.response.status_code} {e.response.text}")
        except Exception as e:
            await ctx.respond(f"An error occurred: {e}")

def setup(bot):
    bot.add_cog(ImageGen(bot))