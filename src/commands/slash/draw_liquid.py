import discord
from discord.ext import commands
from PIL import Image, ImageDraw
import random
import math

class DrawLiquid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="draw_liquid", description='Not Ready Yet')
    async def draw_liquid(self, ctx: discord.ApplicationContext,
        *,
        gradient_size: discord.Option(int, description="Size of the gradient (radius of the circle)") = 500,
        wave_amplitude: discord.Option(float, description="Amplitude of the wave distortion") = 10,
        wave_spacing: discord.Option(float, description="Spacing between waves") = 50,
        ):

        width = 1080
        height = 1080

        try:
            gradient_image = Image.new('RGB', (width, height), (0, 0, 0))
            center_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

            for y in range(height):
                for x in range(width):
                    distorted_x = x + wave_amplitude * math.sin(2 * math.pi * y / wave_spacing)
                    distance_to_center = math.sqrt((distorted_x - width/2)**2 + (y - height/2)**2)
                    normalized_distance = distance_to_center / (gradient_size / 2)
                    normalized_distance = 1 - normalized_distance
                    normalized_distance = max(0, min(1, normalized_distance))
                    r = int(center_color[0] * normalized_distance)
                    g = int(center_color[1] * normalized_distance)
                    b = int(center_color[2] * normalized_distance)
                    gradient_image.putpixel((x, y), (r, g, b))

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