import discord
import numpy as np
import random
import math
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageChops
from noise import pnoise2

fonts = ['Roboto-Black', 'SpaceMono-Regular', 'SpaceMono-Bold', 'Rubik-Bold', 'Arial-Black']
noise_types = ['Perlin', 'Voronoi', 'Turbulence']
presets = ['default', 'vaporwave', 'nebula', 'lava', 'steel']
is_rendering = False

class DrawNoise(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="draw_noise", description='Draw an image using noise')
    async def draw_noise(
        self,
        ctx: discord.ApplicationContext,
        *,
        font: discord.Option(str, description="Select a font.", choices=fonts) = "Roboto-Black",
        text: discord.Option(str = '', description="Enter your text here. Use '/' to split lines.") = None,
        noise_type: discord.Option(str, description="Select a noise style.", choices=noise_types) = "Perlin",
        preset: discord.Option(str, description="Select a preset.", choices=presets) = "default"
    ):
        global is_rendering
        if is_rendering:
            await ctx.respond("Sorry, an image is already being rendered.")
            return

        await ctx.defer()
        is_rendering = True
        try:
            width, height = 1080, 1080
            scale = 300.0
            offset_x = random.uniform(0, 1000)
            offset_y = random.uniform(0, 1000)

            def perlin_noise(x, y):
                return pnoise2(x, y, repeatx=1024, repeaty=1024, base=1)

            def voronoi_noise(x, y):
                cell_size = 50
                gx = int(x // cell_size)
                gy = int(y // cell_size)
                min_dist = float('inf')
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        px = (gx + dx) * cell_size + random.random() * cell_size
                        py = (gy + dy) * cell_size + random.random() * cell_size
                        dist = (x - px) ** 2 + (y - py) ** 2
                        min_dist = min(min_dist, dist)
                return 1 - min_dist / (cell_size * cell_size)

            def turbulence_noise(x, y):
                value = 0
                size = 128
                while size >= 1:
                    value += abs(pnoise2(x / size, y / size, repeatx=1024, repeaty=1024, base=0)) * size
                    size /= 2.0
                return value / 128

            if preset == "vaporwave":
                base_color = (255, 102, 204)
            elif preset == "nebula":
                base_color = (100, 0, 200)
            elif preset == "lava":
                base_color = (255, 70, 0)
            elif preset == "steel":
                base_color = (120, 120, 130)
            else:
                base_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

            r_base, g_base, b_base = base_color
            image = Image.new('RGB', (width, height))
            pixels = image.load()

            for y in range(height):
                for x in range(width):
                    nx = (x + offset_x) / scale
                    ny = (y + offset_y) / scale
                    if noise_type == "Perlin":
                        val = perlin_noise(nx, ny)
                    elif noise_type == "Voronoi":
                        val = voronoi_noise(x, y)
                    elif noise_type == "Turbulence":
                        val = turbulence_noise(x + offset_x, y + offset_y)
                    else:
                        val = 0
                    brightness = int((val + 1) / 2 * 100)
                    r = np.clip(r_base + brightness, 0, 255)
                    g = np.clip(g_base + brightness, 0, 255)
                    b = np.clip(b_base + brightness, 0, 255)
                    pixels[x, y] = (int(r), int(g), int(b))

            if text:
                draw = ImageDraw.Draw(image)
                font_size = int(math.sqrt(width * height) / len(text)) + 25
                font_path = f"miscellaneous/Fonts/{font}.ttf"
                font_obj = ImageFont.truetype(font_path, font_size)
                text_lines = text.split('/')
                text_image = Image.new('RGB', (width, height))
                text_draw = ImageDraw.Draw(text_image)

                line_bboxes = [font_obj.getbbox(line) for line in text_lines]
                line_heights = [bbox[3] - bbox[1] for bbox in line_bboxes]
                total_text_height = sum(line_heights)
                y = (height - total_text_height) // 2

                for line in text_lines:
                    bbox = font_obj.getbbox(line)
                    text_width = bbox[2] - bbox[0]
                    x = (width - text_width) // 2
                    text_draw.text((x, y - bbox[1]), line, fill=(255, 255, 255), font=font_obj)
                    y += bbox[3] - bbox[1]

                image = ImageChops.soft_light(image, text_image)

            image.save('gradient.png')
            file = discord.File('gradient.png')
            embed = discord.Embed(title="Here's your image.", color=discord.Color.from_rgb(*base_color))
            embed.set_image(url="attachment://gradient.png")
            await ctx.respond(file=file, embed=embed)

        except Exception as e:
            try:
                await ctx.respond(f"An error occurred: {str(e)}")
            except discord.NotFound:
                pass
        finally:
            is_rendering = False

def setup(bot):
    bot.add_cog(DrawNoise(bot))