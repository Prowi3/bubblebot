import discord
from discord.ext import commands
from skimage import io
import numpy as np

class DrawTest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="draw_test", description='Generate a black canvas')
    async def draw_test(self, ctx: discord.ApplicationContext,
                        width: discord.Option(int, description="Width of the image") = 1080,
                        height: discord.Option(int, description="Height of the image") = 1080):

        await ctx.defer()

        try:
            canvas = np.zeros((height, width, 3), dtype=np.uint8)

            file_path = 'test.png'
            io.imsave(file_path, canvas)

            file = discord.File(file_path)
            embed = discord.Embed(title="Here's your image", color=discord.Color.dark_theme())
            embed.set_image(url="attachment://test.png")
            await ctx.respond(file=file, embed=embed)

        except Exception as e:
            await ctx.respond(f"An error occurred: {str(e)}", ephemeral=True)

def setup(bot):
    bot.add_cog(DrawTest(bot))
