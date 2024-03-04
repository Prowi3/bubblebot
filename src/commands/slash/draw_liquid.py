import discord
from discord.ext import commands
from PIL import Image, ImageDraw
import random

class DrawLiquid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="draw_liquid", description='Not Ready Yet')
    async def draw_liquid(self, ctx: discord.ApplicationContext,
        *,
        gradient_size: discord.Option(int, description="Size of the gradient (radius of the circle)") = 500,
        ):

        width = 1080

        height = 1080

        try:
            gradient_image = Image.new('RGB', (width, height), (0, 0, 0))


            center_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


            left = (width - gradient_size) // 2
            top = (height - gradient_size) // 2
            right = left + gradient_size
            bottom = top + gradient_size
            ellipse_coords = [(left, top), (right, bottom)]


            draw = ImageDraw.Draw(gradient_image)
            draw.ellipse(ellipse_coords, fill=center_color, outline=None)


            file_path = 'lq.png'
            gradient_image.save(file_path)


            file = discord.File(file_path)
            embed = discord.Embed(title="Here's your image", color=discord.Color.from_rgb(*center_color))
            embed.set_image(url="attachment://lq.png")
            await ctx.respond(file=file, embed=embed)
        
        except Exception as e:
            await ctx.respond(f"An error occurred: {str(e)}")

def setup(bot):
    bot.add_cog(DrawLiquid(bot))
