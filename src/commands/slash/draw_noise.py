import discord
from discord.ext import commands
from discord.commands import Option
from discord import File

import random
import io
import math

from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageEnhance, ImageFilter
import numpy as np
from noise import pnoise2
from opensimplex import OpenSimplex
from scipy.ndimage import gaussian_filter, rotate as scipy_rotate

class DrawNoise(commands.Cog): def init(self, bot): self.bot = bot

def generate_noise(self, width, height, noise_type):
    scale = 50.0
    octaves = 1
    persistence = 0.5
    lacunarity = 2.0
    seed = random.randint(0, 100)

    img = Image.new("RGB", (width, height), (0, 0, 0))
    pixels = img.load()

    for y in range(height):
        for x in range(width):
            nx = x / scale
            ny = y / scale

            if noise_type == "perlin":
                value = noise.pnoise2(nx, ny, octaves=octaves, persistence=persistence, lacunarity=lacunarity, repeatx=width, repeaty=height, base=seed)
                value = int((value + 1) / 2 * 255)
                color = (value, value, value)

            elif noise_type == "voronoi":
                value = int((math.sin(nx + seed) + math.cos(ny + seed)) * 127 + 128)
                r = random.randint(0, 255)
                g = random.randint(0, 255)
                b = random.randint(0, 255)
                color = (value * r // 255, value * g // 255, value * b // 255)

            elif noise_type == "turbulence":
                value = sum([abs(noise.pnoise2(nx * (2 ** i), ny * (2 ** i), base=seed)) / (2 ** i) for i in range(octaves)])
                value = int(min(value * 255, 255))
                r = random.randint(0, 255)
                g = random.randint(0, 255)
                b = random.randint(0, 255)
                color = (value * r // 255, value * g // 255, value * b // 255)

            pixels[x, y] = color

    return img

def apply_effect(self, img, effect):
    if effect == "mirror":
        return ImageChops.difference(img, img.transpose(Image.FLIP_LEFT_RIGHT))
    elif effect == "swirl":
        arr = np.array(img)
        cy, cx = arr.shape[0] // 2, arr.shape[1] // 2
        Y, X = np.indices((arr.shape[0], arr.shape[1]))
        r = np.sqrt((X - cx)**2 + (Y - cy)**2)
        a = np.arctan2(Y - cy, X - cx) + r * 0.002
        Xn = (r * np.cos(a) + cx).astype(int)
        Yn = (r * np.sin(a) + cy).astype(int)
        Xn = np.clip(Xn, 0, arr.shape[1] - 1)
        Yn = np.clip(Yn, 0, arr.shape[0] - 1)
        arr = arr[Yn, Xn]
        return Image.fromarray(arr)
    elif effect == "rgb_split":
        r, g, b = img.split()
        r = r.offset(5, 0)
        b = b.offset(-5, 0)
        return Image.merge("RGB", (r, g, b))
    elif effect == "rotate":
        return img.rotate(30, expand=True)
    elif effect == "invert":
        return ImageChops.invert(img)
    return img

@commands.slash_command(name="draw_noise", description="Draw a noise-based image with optional text.")
async def draw_noise(
    self,
    ctx,
    text: Option(str, "Optional text to draw", required=False),
    noise_type: Option(str, "Type of noise", choices=["perlin", "voronoi", "turbulence"], default="perlin"),
    effect: Option(str, "Visual effect", choices=["none", "mirror", "swirl", "rgb_split", "rotate", "invert"], default="none"),
    font_size: Option(int, "Text size", default=48),
    width: Option(int, "Image width", default=512),
    height: Option(int, "Image height", default=512)
):
    await ctx.defer()

    try:
        img = self.generate_noise(width, height, noise_type)

        if effect != "none":
            img = self.apply_effect(img, effect)

        if text:
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype("DejaVuSans.ttf", font_size)
            text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
            position = ((width - text_width) // 2, (height - text_height) // 2)
            txt_layer = Image.new("RGB", img.size, (0, 0, 0))
            ImageDraw.Draw(txt_layer).text(position, text, font=font, fill=(255, 255, 255))
            img = ImageChops.soft_light(img, txt_layer)

        with io.BytesIO() as image_binary:
            img.save(image_binary, "PNG")
            image_binary.seek(0)
            file = discord.File(fp=image_binary, filename="noise.png")
            embed = discord.Embed(title="Generated Noise")
            embed.set_image(url="attachment://noise.png")
            await ctx.respond(file=file, embed=embed)

    except Exception as e:
        await ctx.respond(f"An error occurred: {str(e)}")

def setup(bot): bot.add_cog(DrawNoise(bot))