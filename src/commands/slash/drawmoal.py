import discord
import numpy as np
import random
import math

from noise import pnoise2
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageChops

fonts = ['Roboto-Black', 'SpaceMono-Regular', 'SpaceMono-Bold', 'Rubik-Bold', 'Arial-Black']
is_rendering = False

class DrawNNoise(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="draw_nnoise", description='Draw an image using Noise')
    async def draw_noise(self, ctx: discord.ApplicationContext):
        global is_rendering

        if is_rendering:
            await ctx.respond("Sorry, an image is already being rendered.")
            return

        is_rendering = True

        await ctx.interaction.response.send_modal(DrawNoiseModal(self))

class DrawNoiseModal(discord.ui.Modal):
    def __init__(self, draw_noise_cog: DrawNoise):
        super().__init__(title="Draw Noise")
        self.draw_noise_cog = draw_noise_cog

        self.font_select = discord.ui.Select(
            placeholder="Select Font",
            options=[discord.SelectOption(label=font) for font in fonts]
        )
        self.text_input = discord.ui.TextInput(
            label="Enter your text (Use '/' to split lines)",
            style=discord.InputTextStyle.long,
            placeholder="Your Text Here"
        )
        self.octaves_input = discord.ui.TextInput(
            label="Octaves (default: 1.0)",
            style=discord.InputTextStyle.short,
            placeholder="1.0"
        )
        self.lacunarity_input = discord.ui.TextInput(
            label="Lacunarity (default: 5.0)",
            style=discord.InputTextStyle.short,
            placeholder="5.0"
        )
        self.persistence_input = discord.ui.TextInput(
            label="Persistence (default: 0.5)",
            style=discord.InputTextStyle.short,
            placeholder="0.5"
        )

        self.add_item(self.font_select)
        self.add_item(self.text_input)
        self.add_item(self.octaves_input)
        self.add_item(self.lacunarity_input)
        self.add_item(self.persistence_input)
    async def callback(self, interaction: discord.Interaction):
        font = self.font_select.values[0]
        text = self.text_input.value or None
        try:
            octaves = float(self.octaves_input.value or 1.0)
            lacunarity = float(self.lacunarity_input.value or 5.0)
            persistence = float(self.persistence_input.value or 0.5)
        except ValueError:
            await interaction.response.send_message(content="Please enter valid numbers for octaves, lacunarity, and persistence.", ephemeral=True)
            return

        await self.draw_noise_cog.draw_noise_with_modal(interaction, font, text, octaves, lacunarity, persistence)

        is_rendering = False

    async def draw_noise_cog(self, interaction, font, text, octaves, lacunarity, persistence):
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

            gradient_image = ImageChops.soft_light(gradient_image, text_image)

        embed_color = discord.Color.from_rgb(*hue_color)

        gradient_image.save('gradient.png')
            
        file_path = 'gradient.png'
        file = discord.File(file_path)
        embed = discord.Embed(title="Here's your image.", color=embed_color)
        embed.set_image(url="attachment://gradient.png")
        await interaction.response.send_message(file=file, embed=embed)

        is_rendering = False

def setup(bot):
    bot.add_cog(DrawNNoise(bot))