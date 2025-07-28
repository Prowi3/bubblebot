import discord
import numpy as np
import random
import math
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter, ImageOps
from noise import pnoise2

fonts = ['Roboto-Black', 'SpaceMono-Regular', 'SpaceMono-Bold', 'Rubik-Bold', 'Arial-Black']
noise_types = ['Perlin', 'Voronoi', 'Turbulence']
presets = ['default', 'vaporwave', 'nebula', 'lava', 'steel']
effects_list = [
    'none', 'mirror', 'wave_distortion', 'swirl', 'rgb_split',
    'invert', 'pixelate', 'blur', 'edge_detect'
]
is_rendering = False

def rgb_split(img, amount=5):
    r, g, b = img.split()
    r = r.offset(amount, 0)
    b = b.offset(-amount, 0)
    return Image.merge("RGB", (r, g, b))

def swirl_effect(img, strength=5):
    width, height = img.size
    center_x, center_y = width / 2, height / 2
    pixels = img.load()
    result = Image.new("RGB", img.size)
    result_pixels = result.load()
    for y in range(height):
        for x in range(width):
            dx = x - center_x
            dy = y - center_y
            distance = math.sqrt(dx*dx + dy*dy)
            angle = math.atan2(dy, dx) + strength * distance / max(width, height)
            src_x = int(center_x + distance * math.cos(angle))
            src_y = int(center_y + distance * math.sin(angle))
            if 0 <= src_x < width and 0 <= src_y < height:
                result_pixels[x, y] = pixels[src_x, src_y]
            else:
                result_pixels[x, y] = (0,0,0)
    return result

def wave_distortion(img, amplitude=10, frequency=20):
    width, height = img.size
    pixels = img.load()
    result = Image.new("RGB", img.size)
    result_pixels = result.load()
    for y in range(height):
        offset = int(amplitude * math.sin(2 * math.pi * y / frequency))
        for x in range(width):
            src_x = x + offset
            if 0 <= src_x < width:
                result_pixels[x, y] = pixels[src_x, y]
            else:
                result_pixels[x, y] = (0, 0, 0)
    return result

def pixelate(img, pixel_size=16):
    small = img.resize((img.width // pixel_size, img.height // pixel_size), resample=Image.NEAREST)
    return small.resize(img.size, Image.NEAREST)

class VoronoiGenerator:
    def __init__(self, width, height, cell_size):
        self.cell_size = cell_size
        self.points = {}
        gx_max = (width // cell_size) + 3
        gy_max = (height // cell_size) + 3
        for gx in range(gx_max):
            for gy in range(gy_max):
                random.seed(gx * 1000 + gy)
                px = gx * cell_size + random.uniform(0, cell_size)
                py = gy * cell_size + random.uniform(0, cell_size)
                self.points[(gx, gy)] = (px, py)

    def noise(self, x, y):
        gx = int(x // self.cell_size)
        gy = int(y // self.cell_size)
        min_dist = float('inf')
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                px, py = self.points.get((gx + dx, gy + dy), (0, 0))
                dist = (x - px) ** 2 + (y - py) ** 2
                if dist < min_dist:
                    min_dist = dist
        return 1 - min_dist / (self.cell_size * self.cell_size)

def turbulence_noise(x, y, octaves=4):
    value = 0
    frequency = 1
    amplitude = 1
    max_value = 0
    for _ in range(octaves):
        value += abs(pnoise2(x * frequency, y * frequency, repeatx=1024, repeaty=1024)) * amplitude
        max_value += amplitude
        amplitude /= 2
        frequency *= 2
    return value / max_value

class DrawNoise(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="draw_noise", description='Draw an image using noise with effects')
    async def draw_noise(
        self,
        ctx: discord.ApplicationContext,
        *,
        font: discord.Option(str, description="Select a font.", choices=fonts) = "Roboto-Black",
        text: discord.Option(str = '', description="Enter your text here. Use '/' to split lines.") = None,
        noise_type: discord.Option(str, description="Select a noise style.", choices=noise_types) = "Perlin",
        preset: discord.Option(str, description="Select a preset.", choices=presets) = "default",
        effect: discord.Option(str, description="Select an effect.", choices=effects_list) = "none"
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

            OCTAVES = 1
            PERSISTENCE = 0.5
            LACUNARITY = 5.0

            voronoi_gen = VoronoiGenerator(width, height, cell_size=50)

            def perlin_noise(x, y):
                return pnoise2(x, y, octaves=OCTAVES, persistence=PERSISTENCE, lacunarity=LACUNARITY, repeatx=1024, repeaty=1024, base=1)

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
                        brightness = int((val + 1) / 2 * 180)
                    elif noise_type == "Voronoi":
                        val = voronoi_gen.noise(x, y)
                        brightness = int(val * 255)
                    elif noise_type == "Turbulence":
                        val = turbulence_noise(nx, ny, octaves=4)
                        brightness = int(val * 255)
                    else:
                        brightness = 0
                    r = np.clip(r_base + brightness, 0, 255)
                    g = np.clip(g_base + brightness, 0, 255)
                    b = np.clip(b_base + brightness, 0, 255)
                    pixels[x, y] = (int(r), int(g), int(b))

            if text:
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

            if effect == "mirror":
                image = ImageOps.mirror(image)
            elif effect == "wave_distortion":
                image = wave_distortion(image)
            elif effect == "swirl":
                image = swirl_effect(image)
            elif effect == "rgb_split":
                image = rgb_split(image)
            elif effect == "invert":
                image = ImageOps.invert(image)
            elif effect == "pixelate":
                image = pixelate(image)
            elif effect == "blur":
                image = image.filter(ImageFilter.GaussianBlur(radius=5))
            elif effect == "edge_detect":
                image = image.filter(ImageFilter.FIND_EDGES)

            image.save('gradient.png')
            file = discord.File('gradient.png')
            embed = discord.Embed(title="Here's your noise art with effects!", color=discord.Color.from_rgb(*base_color))
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