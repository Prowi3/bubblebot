import discord
from discord.ext import commands
from PIL import Image

class DrawLiquid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="draw_liquid", description='Not Ready Yet')
    async def draw_noise(self, ctx: discord.ApplicationContext,
        *,
        width: discord.Option(int, description="Width of the image") = 1080,
        height: discord.Option(int, description="Height of the image") = 1080,
        ):

        try:
            blank_image = Image.new('RGB', (width, height), (255, 255, 255))

            file_path = 'lq.png'
            blank_image.save(file_path)

            file = discord.File(file_path)

            embed = discord.Embed(title="Here's your image", color=discord.Color.from_rgb(255, 255, 255))
            embed.set_image(url="attachment://lq.png")

            await ctx.respond(file=file, embed=embed)
        
        except Exception as e:
            await ctx.respond(f"An error occurred: {str(e)}")

def setup(bot):
    bot.add_cog(DrawLiquid(bot))
