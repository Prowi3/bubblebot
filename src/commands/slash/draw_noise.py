import discord
import numpy as np
import random
import math
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageChops
from noise import pnoise2

fonts = ['Roboto-Black', 'SpaceMono-Regular', 'SpaceMono-Bold', 'Rubik-Bold', 'Arial-Black']
presets = {
    "Vibrant Turbulence": {"octaves": 6, "lacunarity": 2.2, "persistence": 0.55, "noise_type": "turbulence"},
    "Electric Storm": {"octaves": 3, "lacunarity": 4.0, "persistence": 0.4, "noise_type": "turbulence"},
    "Crystal Grid": {"octaves": 1, "lacunarity": 2.0, "persistence": 0.9, "noise_type": "voronoi"},
    "Alien Bloom": {"octaves": 4, "lacunarity": 3.5, "persistence": 0.6, "noise_type": "voronoi"}
}
noise_types = ["perlin", "turbulence", "voronoi"]
is_rendering = False

class DrawNoise(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="draw_noise", description='Draw an image using cool noise effects')
    async def draw_noise(
        self,
        ctx: discord.ApplicationContext,
        *,
        font: discord.Option(str, description="Select a font.", choices=fonts) = "Roboto-Black",
        text: discord.Option(str = '',  description="Enter your text. Use '/' for line breaks.") = None,
        preset: discord.Option(str, choices=list(presets.keys()), description="Select a preset.") = None,
        noise_type: discord.Option(str, description="Choose the noise type", choices=noise_types) = "perlin",
        octaves: discord.Option(int, description="Octave amount") = 1, 
        lacunarity: discord.Option(float , description="Lacunarity value") = 5.0,
        persistence: discord.Option(float , description="Persistence value") = 0.5
    ):
        global is_rendering
        if is_rendering:
            await ctx.respond("Sorry, an image is already being rendered.")
            return

        is_rendering = True
        try:
            if preset:
                preset_data = presets[preset]
                octaves = preset_data["octaves"]
                lacunarity = preset_data["lacunarity"]
                persistence = preset_data["persistence"]
                noise_type = preset_data["noise_type"]

            width, height = 1080, 1080
            scale = 300.0
            hue_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            offset_x = random.uniform(0, 1000)
            offset_y = random.uniform(0, 1000)

            def generate_noise(x, y):
                if noise_type == "perlin":
                    return pnoise2(x / scale, y / scale, octaves=octaves, persistence=persistence, lacunarity=lacunarity, repeatx=1024, repeaty=1024, base=1)
                elif noise_type == "turbulence":
                    val = sum(abs(pnoise2((x / scale) * lacunarity ** i, (y / scale) * lacunarity ** i)) * persistence ** i for i in range(octaves))
                    return val
                elif noise_type == "voronoi":
                    cell_size = 40
                    cell_x = int(x // cell_size)
                    cell_y = int(y // cell_size)
                    min_dist = float('inf')
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            cx = (cell_x + dx) * cell_size + cell_size // 2
                            cy = (cell_y + dy) * cell_size + cell_size // 2
                            dist = (x - cx)**2 + (y - cy)**2
                            if dist < min_dist:
                                min_dist = dist
                    return 1.0 - min_dist / (cell_size ** 2)

            image = Image.new('RGB', (width, height))
            pixels = image.load()

            for y in range(height):
                for x in range(width):
                    noise_val = generate_noise(x + offset_x, y + offset_y)
                    r = np.clip(hue_color[0] + noise_val * 100, 0, 255)
                    g = np.clip(hue_color[1] + noise_val * 100, 0, 255)
                    b = np.clip(hue_color[2] + noise_val * 100, 0, 255)
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

                for i, line in enumerate(text_lines):
                    bbox = font_obj.getbbox(line)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (width - text_width) // 2
                    text_draw.text((x, y - bbox[1]), line, fill=(255, 255, 255), font=font_obj)
                    y += text_height

                image = ImageChops.soft_light(image, text_image)

            embed_color = discord.Color.from_rgb(*hue_color)
            image.save('gradient.png')
            file = discord.File('gradient.png')
            embed = discord.Embed(title="Here's your noise art!", color=embed_color)
            embed.set_image(url="attachment://gradient.png")
            await ctx.respond(file=file, embed=embed)

        except Exception as e:
            await ctx.respond(f"Error: {str(e)}")

        finally:
            is_rendering = False

def setup(bot):
    bot.add_cog(DrawNoise(bot))