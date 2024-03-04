import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageChops
import random
import math

class DrawLiquid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    fonts = ['Roboto-Black', 'SpaceMono-Regular', 'SpaceMono-Bold', 'Rubik-Bold', 'Arial-Black']

    @commands.slash_command(name="draw_liquid", description='Not Ready Yet')
    async def draw_liquid(self, ctx: discord.ApplicationContext,
        *,
        font: discord.Option(str, description="Select a font.", choices=fonts) = "Roboto-Black",
        text: discord.Option(str, description="Enter your text here. Use '/' to split lines. Emojis and emotes won't work.") = None,
        gradient_size: discord.Option(int, description="Size of the gradient (radius of the circle)") = 900,
        wave_amplitude: discord.Option(float, description="Amplitude of the wave distortion") = 150,
        wave_spacing: discord.Option(float, description="Spacing between waves") = 125,
        wave_angle: discord.Option(float, description="Angle of the wave distortion (in degrees)") = 0,
        swirl_strength: discord.Option(float, description="Strength of the swirl distortion") = 6,
        swirl_radius: discord.Option(float, description="Radius of the swirl distortion") = 500,
        ):

        await ctx.defer()

        width = 1080
        height = 1080

        wave_angle_rad = math.radians(wave_angle)

        try:
            gradient_image = Image.new('RGB', (width, height), (0, 0, 0))
            center_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

            for y in range(height):
                for x in range(width):
                    dx = x - width / 2
                    dy = y - height / 2
                    distorted_x = x + wave_amplitude * math.sin(2 * math.pi * (dx * math.cos(wave_angle_rad) + dy * math.sin(wave_angle_rad)) / wave_spacing)
                    
                    distance_to_center = math.sqrt((distorted_x - width/2)**2 + (y - height/2)**2)
                    normalized_distance = distance_to_center / (gradient_size / 2)
                    normalized_distance = 1 - normalized_distance
                    normalized_distance = max(0, min(1, normalized_distance))
                    r = int(center_color[0] * normalized_distance)
                    g = int(center_color[1] * normalized_distance)
                    b = int(center_color[2] * normalized_distance)
                    gradient_image.putpixel((x, y), (r, g, b))
                    
            swirl_image = gradient_image.copy()
            for y in range(height):
                for x in range(width):
                    dx = x - width / 2
                    dy = y - height / 2
                    r = math.sqrt(dx ** 2 + dy ** 2)
                    angle = math.atan2(dy, dx)
                    angle += swirl_strength * r / swirl_radius
                    new_x = width / 2 + r * math.cos(angle)
                    new_y = height / 2 + r * math.sin(angle)
                    if 0 <= new_x < width and 0 <= new_y < height:
                        gradient_image.putpixel((x, y), swirl_image.getpixel((int(new_x), int(new_y))))

            if text:
                draw = ImageDraw.Draw(gradient_image)
                font_size = int(math.sqrt(width * height) / len(text)) + 25
                font_path = f"miscellaneous/Fonts/{font}.ttf"
                font = ImageFont.truetype(font_path, font_size)
                text_lines = text.split('/')
                
                max_text_width = 0
                total_text_height = 0
                for line in text_lines:
                    text_width, text_height = draw.textsize(line, font=font)
                    if text_width > max_text_width:
                        max_text_width = text_width
                    total_text_height += text_height
                
                x = round((width - max_text_width) / 2) + 1
                y = round((height - total_text_height) / 2) + 2
                text_image = Image.new('RGB', (width, height))
                for line in text_lines:
                    text_width, text_height = draw.textsize(line, font=font)
                    line_x = round((width - text_width) / 2)
                    text_draw = ImageDraw.Draw(text_image)
                    text_draw.text((line_x, y), text=line, fill=(255, 255, 255), font=font)
                    y += text_height
                
                gradient_image = ImageChops.soft_light(text_image, gradient_image)

            file_path = 'lq.png'
            gradient_image.save(file_path)
            file = discord.File(file_path)
            embed = discord.Embed(title="Here's your image", color=discord.Color.from_rgb(*center_color))
            embed.set_image(url="attachment://lq.png")
            await ctx.respond(file=file, embed=embed)
        
        except Exception as e:
            await ctx.respond(f"An error occurred: {str(e)}", ephemeral=True)

def setup(bot):
    bot.add_cog(DrawLiquid(bot))
