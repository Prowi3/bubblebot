import discord

import httpx
import numpy as np
import random
import math

from noise import pnoise2
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageChops

fonts = ['Roboto-Black', 'SpaceMono-Regular', 'SpaceMono-Bold', 'DancingScript-Bold', 'Rubik-Bold', 'Arial-Black']
is_rendering = False

class DrawNoise(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="draw_noise", description='Draw an image using Noise')
    async def draw_noise(self, ctx: discord.ApplicationContext,
        font: discord.Option(str, description="Select a font.", choices=fonts), *,
        text: discord.Option(str = '',  description="Enter your text here. emojis and emots won't work.") = None,
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
            noise_values = pnoise2_vectorized(x_coords / scale, y_coords / scale, octaves = octaves, persistence = persistence, lacunarity = lacunarity, repeatx=1024, repeaty=1024, base=1)
            
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
                text_width, text_height = draw.textsize(text, font=font)
                x = round((width - text_width) / 2) + 1
                y = round((height - text_height) / 2) + 2
                text_image = Image.new('RGB', (width, height))
                text_draw = ImageDraw.Draw(text_image)
                text_draw.text((x, y), text=text, fill=(255, 255, 255), font=font)

                gradient_image = ImageChops.soft_light(gradient_image, text_image)
            
            embed_color = discord.Color.from_rgb(*hue_color)

            gradient_image.save('gradient.png')
            
            file_path = 'gradient.png'
            file = discord.File(file_path)
            embed = discord.Embed(title="Here's your image.", color=embed_color)
            embed.set_image(url="attachment://gradient.png")
            await ctx.respond(file=file, embed=embed)

            is_rendering = False
        
        except Exception as e:
            is_rendering = False
            await ctx.respond(f"An error occurred: {str(e)}")

def setup(bot):
    bot.add_cog(DrawNoise(bot))