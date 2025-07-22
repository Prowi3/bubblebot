import discord
import numpy as np
import random
import math

from noise import pnoise2
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageChops

fonts = ['Roboto-Black', 'SpaceMono-Regular', 'SpaceMono-Bold', 'Rubik-Bold', 'Arial-Black']
is_rendering = False

class DrawNoise(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="draw_noise", description='Draw an image using Noise')
    async def draw_noise(self, ctx: discord.ApplicationContext,
        *,
        font: discord.Option(str, description="Select a font.", choices=fonts) = "Roboto-Black",
        text: discord.Option(str = '',  description="Enter your text here. Use '/' to split lines. emojis and emots won't work.") = None,
        octaves: discord.Option(int, description="Choose the octave amount, the default is 1.0 (/help for more info)") = 1, 
        lacunarity: discord.Option(float , description="Choose the lacunarity amount, the default is 5.0 (/help for more info)") = 5.0,
        persistence: discord.Option(float , description="Choose the persistence amount, the default is to 0.5 (/help for more info)") = 0.5
        ):

        global is_rendering
        
        if is_rendering:
            await ctx.send("Sorry, an image is already being rendered.")
            return
        
        is_rendering = True
        await ctx.defer()
        
        try:
            width, height = 1080, 1080
            gradient_image = Image.new('RGB', (width, height))
            draw = ImageDraw.Draw(gradient_image)
            
            scale = 300.0
            hue_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

            offset_x = random.uniform(0, 1000)
            offset_y = random.uniform(0, 1000)
            
            x_coords = np.arange(width) + offset_x
            y_coords = np.arange(height) + offset_y
            x_coords, y_coords = np.meshgrid(x_coords, y_coords)
            
            pnoise2_vectorized = np.vectorize(pnoise2)
            noise_values = pnoise2_vectorized(x_coords / scale, y_coords / scale, octaves=octaves, persistence=persistence, lacunarity=lacunarity, repeatx=1024, repeaty=1024, base=1)
            
            r, g, b = hue_color
            r_values = np.clip(r + noise_values * 100, 0, 255).astype(np.uint8)
            g_values = np.clip(g + noise_values * 100, 0, 255).astype(np.uint8)
            b_values = np.clip(b + noise_values * 100, 0, 255).astype(np.uint8)
            rgb_values = np.stack([r_values, g_values, b_values], axis=-1)
            gradient_image = Image.fromarray(rgb_values)

            if text:
                draw = ImageDraw.Draw(gradient_image)
                font_size = int(math.sqrt(width * height) / len(text)) + 25
                font_path = f"miscellaneous/Fonts/{font}.ttf"
                font = ImageFont.truetype(font_path, font_size)
                text_lines = text.split('/')

                text_image = Image.new('RGB', (width, height))
                text_draw = ImageDraw.Draw(text_image)

                line_heights = [draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] for line in text_lines]
                total_text_height = sum(line_heights)

                y = (height - total_text_height) // 2

                for i, line in enumerate(text_lines):
                    bbox = text_draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = line_heights[i]
                    x = (width - text_width) // 2
                    text_draw.text((x, y), line, fill=(255, 255, 255), font=font)
                    y += text_height

                gradient_image = ImageChops.soft_light(gradient_image, text_image)

            embed_color = discord.Color.from_rgb(*hue_color)

            gradient_image.save('gradient.png')
            file_path = 'gradient.png'
            file = discord.File(file_path)
            embed = discord.Embed(title="Here's your image.", color=embed_color)
            embed.set_image(url="attachment://gradient.png")
            await ctx.respond(file=file, embed=embed)

        except Exception as e:
            await ctx.respond(f"An error occurred: {str(e)}")
        finally:
            is_rendering = False

def setup(bot):
    bot.add_cog(DrawNoise(bot))