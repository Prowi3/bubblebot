import discord
from discord.ext import commands
import os
import io
import asyncio
import base64
from craiyon import Craiyon, craiyon_utils
from dotenv import load_dotenv

load_dotenv()

class ImageGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.generator = Craiyon()

    @commands.slash_command(name="imagine", description="Generate images using Craiyon (free)")
    async def imagine(self, ctx: discord.ApplicationContext, prompt: str):
        await ctx.defer()

        try:
            result = await self.generator.async_generate(prompt)
            b64_list = await craiyon_utils.async_encode_base64(result.images)

            images = []
            for b64 in b64_list:
                img_bytes = io.BytesIO(base64.b64decode(b64))
                images.append(discord.File(img_bytes, filename="image.png"))

            index = 0

            embed = discord.Embed(
                title=f"Image 1/9",
                description=f"`{prompt}`",
                color=0x00B2FF
            )
            embed.set_image(url="attachment://image.png")

            class ImageView(discord.ui.View):
                def __init__(self, images):
                    super().__init__(timeout=300)
                    self.images = images
                    self.index = 0

                @discord.ui.button(label="Prev", style=discord.ButtonStyle.secondary)
                async def prev(self, button, interaction):
                    self.index = (self.index - 1) % len(self.images)
                    await self.update(interaction)

                @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
                async def next(self, button, interaction):
                    self.index = (self.index + 1) % len(self.images)
                    await self.update(interaction)

                async def update(self, interaction):
                    embed = discord.Embed(
                        title=f"Image {self.index + 1}/{len(self.images)}",
                        description=f"`{prompt}`",
                        color=0x00B2FF
                    )
                    embed.set_image(url="attachment://image.png")
                    await interaction.response.edit_message(embed=embed, attachments=[self.images[self.index]], view=self)

            view = ImageView(images)
            await ctx.respond(embed=embed, file=images[0], view=view)

        except Exception as e:
            await ctx.respond(f"Error generating from Craiyon: `{e}`")

def setup(bot):
    bot.add_cog(ImageGen(bot))