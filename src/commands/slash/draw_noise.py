import discord
import numpy as np
import random
import math
import os
from noise import pnoise2, snoise2
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageChops

fonts = ['Roboto-Black', 'SpaceMono-Regular', 'SpaceMono-Bold', 'Rubik-Bold', 'Arial-Black']

presets = {
    "Inferno": {
        "color": (255, 60, 0),
        "octaves": 4,
        "lacunarity": 3.0,
        "persistence": 0.7,
        "scale": 180.0,
        "noise_type": "perlin"
    },
    "Nebula": {
        "color": (128, 0, 255),
        "octaves": 6,
        "lacunarity": 2.5,
        "persistence": 0.6,
        "scale": 250.0,
        "noise_type": "perlin"
    },
    "Frostbite": {
        "color": (200, 240, 255),
        "octaves": 6,
        "lacunarity": 4.0,
        "persistence": 0.4,
        "scale": 120.0,
        "noise_type": "simplex"
    },
    "Toxic": {
        "color": (80, 255, 80),
        "octaves": 8,
        "lacunarity": 5.0,
        "persistence": 0.3,
        "scale": 140.0,
        "noise_type": "simplex"
    },
    "Crimson": {
        "color": (180, 20, 30),
        "octaves": 5,
        "lacunarity": 2.8,
        "persistence": 0.5,
        "scale": 240.0,
        "noise_type": "perlin"
    },
    "Dream": {
        "color": (255, 200, 255),
        "octaves": 3,
        "lacunarity": 1.8,
        "persistence": 0.4,
        "scale": 270.0,
        "noise_type": "value"
    },
    "Static": {
        "color": (180, 180, 180),
        "octaves": 1,
        "lacunarity": 2.0,
        "persistence": 0.3,
        "scale": 100.0,
        "noise_type": "value"
    },
    "Cosmic": {
        "color": (50, 10, 100),
        "octaves": 6,
        "lacunarity": 3.5,
        "persistence": 0.7,
        "scale": 160.0,
        "noise_type": "simplex"
    },
    "Void": {
        "color": (10, 10, 10),
        "octaves": 1,
        "lacunarity": 2.0,
        "persistence": 0.4,
        "scale": 180.0,
        "noise_type": "none"
    },
    "Turbulence": {
        "color": (100, 120, 200),
        "octaves": 4,
        "lacunarity": 3.0,
        "persistence": 0.5,
        "scale": 150.0,
        "noise_type": "turbulence"
    },
    "Voronoi": {
        "color": (40, 200, 150),
        "octaves": 1,
        "lacunarity": 2.0,
        "persistence": 0.5,
        "scale": 25.0,
        "noise_type": "voronoi"
    }
}

is_rendering = False

def generate_value_noise(width, height, scale, seed=0):
    random.seed(seed)
    grid_size = int(scale)
    grid = np.random.rand(grid_size + 1, grid_size + 1)
    def lerp(a, b, t):
        return a + t * (b - a)
    def smoothstep(t):
        return t * t * (3 - 2 * t)
    noise = np.zeros((height, width))
    for y in range(height):
        for x in range(width):
            gx = (x / width) * grid_size
            gy = (y / height) * grid_size
            ix = int(gx)
            iy = int(gy)
            fx = gx - ix
            fy = gy - iy

            v00 = grid[iy][ix]
            v10 = grid[iy][ix + 1]
            v01 = grid[iy + 1][ix]
            v11 = grid[iy + 1][ix + 1]

            wx = smoothstep(fx)
            wy = smoothstep(fy)

            nx0 = lerp(v00, v10, wx)
            nx1 = lerp(v01, v11, wx)
            nxy = lerp(nx0, nx1, wy)

            noise[y, x] = nxy
    return noise * 2 - 1

def generate_voronoi_noise(width, height, scale, points_count=50, seed=0):
    random.seed(seed)
    points = [(random.uniform(0, width), random.uniform(0, height)) for _ in range(points_count)]
    noise = np.zeros((height, width))
    for y in range(height):
        for x in range(width):
            distances = [math.hypot(x - px, y - py) for px, py in points]
            noise[y, x] = min(distances)
    noise = noise / noise.max()
    noise = 1.0 - noise
    noise = noise * 2 - 1
    return noise

class DrawNoise(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="draw_noise", description="Draw an image using noise and optional text.")
    async def draw_noise(
        self,
        ctx: discord.ApplicationContext,
        *,
        font: discord.Option(str, description="Pick a font", choices=fonts) = "Roboto-Black",
        text: discord.Option(str = '', description="Enter your text. Use '/' for line breaks. Emojis not supported.") = None,
        octaves: discord.Option(int, description="Noise detail level (1–10, default 1)") = 1,
        lacunarity: discord.Option(float, description="Noise frequency (default 5.0)") = 5.0,
        persistence: discord.Option(float, description="Noise strength (default 0.5)") = 0.5,
        preset: discord.Option(str, description="Choose a visual theme", choices=["None"] + list(presets.keys())) = "None",
        noise_type: discord.Option(str, description="Noise algorithm to use", choices=["perlin", "simplex", "value", "voronoi", "none", "turbulence"]) = "perlin"
    ):
        global is_rendering
        if is_rendering:
            await ctx.respond("Please wait, another image is rendering.")
            return

        is_rendering = True
        await ctx.defer()

        try:
            width, height = 1080, 1080

            if preset != "None" and preset in presets:
                preset_config = presets[preset]
                hue_color = preset_config["color"]
                octaves = preset_config["octaves"]
                lacunarity = preset_config["lacunarity"]
                persistence = preset_config["persistence"]
                scale = preset_config["scale"]
                noise_type = preset_config.get("noise_type", noise_type)
            else:
                hue_color = tuple(random.randint(0, 255) for _ in range(3))
                scale = 300.0

            offset_x = random.uniform(0, 1000)
            offset_y = random.uniform(0, 1000)

            x_coords, y_coords = np.meshgrid(
                np.arange(width) + offset_x,
                np.arange(height) + offset_y
            )

            def normalize(arr):
                arr_min = arr.min()
                arr_max = arr.max()
                if arr_max - arr_min == 0:
                    return np.zeros_like(arr)
                return (arr - arr_min) / (arr_max - arr_min) * 2 - 1

            if noise_type == "perlin":
                pnoise2_vectorized = np.vectorize(pnoise2)
                noise_vals = pnoise2_vectorized(
                    x_coords / scale,
                    y_coords / scale,
                    octaves=octaves,
                    persistence=persistence,
                    lacunarity=lacunarity,
                    repeatx=1024,
                    repeaty=1024,
                    base=1
                )
                noise_vals = normalize(noise_vals)

            elif noise_type == "simplex":
                snoise2_vectorized = np.vectorize(snoise2)
                noise_vals = snoise2_vectorized(
                    x_coords / scale,
                    y_coords / scale,
                    octaves=octaves,
                    persistence=persistence,
                    lacunarity=lacunarity,
                    repeatx=1024,
                    repeaty=1024,
                    base=1
                )
                noise_vals = normalize(noise_vals)

            elif noise_type == "value":
                noise_vals = generate_value_noise(width, height, scale, seed=random.randint(0, 10000))

            elif noise_type == "voronoi":
                noise_vals = generate_voronoi_noise(width, height, scale, points_count=75, seed=random.randint(0, 10000))

            elif noise_type == "turbulence":
                pnoise2_vectorized = np.vectorize(pnoise2)
                snoise2_vectorized = np.vectorize(snoise2)

                perlin_noise = pnoise2_vectorized(
                    x_coords / scale,
                    y_coords / scale,
                    octaves=octaves,
                    persistence=persistence,
                    lacunarity=lacunarity,
                    repeatx=1024,
                    repeaty=1024,
                    base=1
                )

                simplex_noise = snoise2_vectorized(
                    x_coords / (scale / 2),
                    y_coords / (scale / 2),
                    octaves=octaves,
                    persistence=persistence / 2,
                    lacunarity=lacunarity,
                    repeatx=1024,
                    repeaty=1024,
                    base=42
                )

                combined = (perlin_noise + simplex_noise) / 2.0
                noise_vals = normalize(combined)

            else:  # none
                noise_vals = np.zeros((height, width))

            r, g, b = hue_color
            rgb = np.clip(np.stack([
                r + noise_vals * 100,
                g + noise_vals * 100,
                b + noise_vals * 100
            ], axis=-1), 0, 255).astype(np.uint8)

            img = Image.fromarray(rgb)

            if text:
                font_path = f"miscellaneous/Fonts/{font}.ttf"
                text_lines = text.split('/')
                line_count = len(text_lines)
                font_size = max(24, int(math.sqrt(width * height) / (sum(len(line) for line in text_lines) / line_count + 5)))

                try:
                    font_obj = ImageFont.truetype(font_path, font_size)
                except Exception:
                    font_obj = ImageFont.load_default()

                text_img = Image.new('RGB', (width, height), (0, 0, 0))
                draw = ImageDraw.Draw(text_img)

                y_offset = (height - (font_size * line_count)) // 2
                for line in text_lines:
                    bbox = font_obj.getbbox(line)
                    line_width = bbox[2] - bbox[0]
                    x = (width - line_width) // 2
                    draw.text((x, y_offset), line, font=font_obj, fill=(255, 255, 255))
                    y_offset += font_size + 10

                img = ImageChops.soft_light(img, text_img)

            temp_path = "generated_noise.png"
            img.save(temp_path)

            embed = discord.Embed(title="Here is your image.", color=discord.Color.from_rgb(*hue_color))
            if preset != "None":
                embed.description = f"Preset: {preset}"
            embed.set_image(url="attachment://generated_noise.png")

            await ctx.respond(file=discord.File(temp_path), embed=embed)

            os.remove(temp_path)

        except Exception as e:
            await ctx.respond(f"Error: {e}")
        finally:
            is_rendering = False

def setup(bot):
    bot.add_cog(DrawNoise(bot))