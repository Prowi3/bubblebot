import discord
import numpy as np
import random
import math
from noise import pnoise2
from discord.ext import commands
from discord.ui import View, Button, Select
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

fonts = ['Roboto-Black', 'SpaceMono-Regular', 'SpaceMono-Bold', 'Rubik-Bold', 'Arial-Black']
patterns = ['classic', 'swirl', 'ripple', 'concentric', 'marble', 'voronoi', 'turbulence', 'waves']
aspect_ratios = ["1:1", "16:9", "4:3", "9:16", "21:9"]
DEFAULT_OCTAVES = 3
DEFAULT_LACUNARITY = 2.0
DEFAULT_PERSISTENCE = 0.5

is_rendering = False

def generate_noise_image(params):
    w_ratio, h_ratio = map(int, params['aspect_ratio'].split(":"))
    max_size = 1080
    if w_ratio >= h_ratio:
        w = max_size
        h = int(max_size * (h_ratio / w_ratio))
    else:
        h = max_size
        w = int(max_size * (w_ratio / h_ratio))

    scale = random.uniform(180.0, 380.0)
    color = tuple(random.randint(25, 230) for _ in range(3))
    ox, oy = random.uniform(0, 2000), random.uniform(0, 2000)
    xs = np.arange(w, dtype=np.float32) - (w / 2) + ox
    ys = np.arange(h, dtype=np.float32) - (h / 2) + oy
    xx, yy = np.meshgrid(xs, ys)

    pattern = params['pattern']
    if pattern == "swirl":
        r = np.sqrt(xx**2 + yy**2) + 1e-6
        theta = np.arctan2(yy, xx)
        twist = 0.8 + random.uniform(0.0, 1.2)
        theta = theta + twist * (r / max(w, h)) * 6.0
        xx = r * np.cos(theta)
        yy = r * np.sin(theta)
        xx += np.sin(yy / 15.0) * 8.0
        yy += np.cos(xx / 15.0) * 8.0
    elif pattern == "ripple":
        xx += np.sin(yy / 12.0) * 18.0
        yy += np.sin(xx / 18.0) * 12.0
        xx += np.sin(xx / 40.0 + yy / 60.0) * 6.0
    elif pattern == "concentric":
        dist = np.sqrt((xx)**2 + (yy)**2)
        xx += np.sin(dist / 12.0) * 22.0
        yy += np.cos(dist / 12.0) * 22.0
    elif pattern == "marble":
        xx += np.sin(xx / 28.0) * 48.0
        yy += np.sin(yy / 40.0) * 10.0
    elif pattern == "voronoi":
        offsets = []
        for i in range(6):
            offsets.append(np.stack([xx + random.uniform(-40, 40), yy + random.uniform(-40, 40)], axis=0))
        disp = sum(np.sin(o[0] / 30.0) + np.cos(o[1] / 30.0) for o in offsets)
        xx += disp * 6.0
        yy += disp * 6.0
    elif pattern == "turbulence":
        turb = np.zeros_like(xx)
        amp = 1.0
        freq = 1.0
        for i in range(4):
            turb += amp * np.sin((xx * freq) / (20.0 + i * 6.0)) * np.cos((yy * freq) / (18.0 + i * 6.0))
            amp *= 0.5
            freq *= 2.0
        xx += turb * 20.0
        yy += (turb * 14.0)
    elif pattern == "waves":
        xx += np.sin(yy / 10.0 + np.sin(xx / 60.0)) * 20.0
        yy += np.cos(xx / 14.0 + np.cos(yy / 50.0)) * 10.0

    def perlin_grid(xarr, yarr):
        return np.vectorize(lambda a, b: pnoise2(a, b,
                                                octaves=DEFAULT_OCTAVES,
                                                persistence=DEFAULT_PERSISTENCE,
                                                lacunarity=DEFAULT_LACUNARITY,
                                                repeatx=4096, repeaty=4096, base=0),
                            otypes=[float])(xarr, yarr)

    noise = perlin_grid(xx / scale, yy / scale)
    noise_scaled = (noise - noise.min()) / (noise.max() - noise.min() + 1e-9)
    r = np.clip(color[0] + (noise_scaled - 0.5) * 220, 0, 255).astype(np.uint8)
    g = np.clip(color[1] + (noise_scaled - 0.5) * 220, 0, 255).astype(np.uint8)
    b = np.clip(color[2] + (noise_scaled - 0.5) * 220, 0, 255).astype(np.uint8)
    img = Image.fromarray(np.dstack([r, g, b]), 'RGB')

    if params['gradient']:
        grad = Image.new("RGB", (w, h))
        grad_draw = ImageDraw.Draw(grad)
        c1 = tuple(random.randint(0, 255) for _ in range(3))
        c2 = tuple(random.randint(0, 255) for _ in range(3))
        for y in range(h):
            blend = y / (h - 1)
            grad_color = tuple(int(c1[i] * (1 - blend) + c2[i] * blend) for i in range(3))
            grad_draw.line([(0, y), (w, y)], fill=grad_color)
        img = ImageChops.overlay(img, grad)

    if params['text']:
        lines = params['text'].split('/')
        longest = max(lines, key=len)
        font_size = max(28, int((w / max(1, len(longest))) * 0.9))
        font_path = f"miscellaneous/Fonts/{params['font']}.ttf"
        fnt = ImageFont.truetype(font_path, font_size)
        txt = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        tdraw = ImageDraw.Draw(txt)
        bboxes = [fnt.getbbox(l) for l in lines]
        heights = [b[3] - b[1] for b in bboxes]
        total_h = sum(heights) + (len(lines) - 1) * 10
        ty = (h - total_h) // 2
        for line in lines:
            bbox = fnt.getbbox(line)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            tx = (w - tw) // 2
            if params['glow']:
                glow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                glow_draw = ImageDraw.Draw(glow_layer)
                glow_color = tuple(min(255, int(c * 1.4)) for c in color) + (180,)
                glow_draw.text((tx, ty - bbox[1]), line, font=fnt, fill=glow_color)
                for _ in range(4):
                    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(6))
                img = Image.alpha_composite(img.convert('RGBA'), glow_layer).convert('RGB')
            tdraw.text((tx, ty - bbox[1]), line, fill=(255, 255, 255, 255), font=fnt)
            ty += th + 10
        img = ImageChops.soft_light(img, txt.convert('RGB'))

    if params['grain']:
        grain_layer = np.random.randint(0, 60, (h, w, 3), dtype=np.uint8)
        img = ImageChops.add(img, Image.fromarray(grain_layer))

    return img

class NoiseControls(View):
    def __init__(self, params):
        super().__init__(timeout=180)
        self.params = params

        self.pattern_select = Select(placeholder="Pattern", options=[
            discord.SelectOption(label=p, default=(p==self.params['pattern'])) for p in patterns
        ], custom_id="pattern_select")
        self.pattern_select.callback = self.pattern_changed
        self.add_item(self.pattern_select)

        self.aspect_select = Select(placeholder="Aspect Ratio", options=[
            discord.SelectOption(label=ar, default=(ar==self.params['aspect_ratio'])) for ar in aspect_ratios
        ], custom_id="aspect_select")
        self.aspect_select.callback = self.aspect_changed
        self.add_item(self.aspect_select)

        self.font_select = Select(placeholder="Font", options=[
            discord.SelectOption(label=f, default=(f==self.params['font'])) for f in fonts
        ], custom_id="font_select")
        self.font_select.callback = self.font_changed
        self.add_item(self.font_select)

        self.glow_button = Button(label=f"Glow: {'On' if self.params['glow'] else 'Off'}", custom_id="toggle_glow", style=discord.ButtonStyle.primary)
        self.glow_button.callback = self.toggle_glow
        self.add_item(self.glow_button)

        self.gradient_button = Button(label=f"Gradient: {'On' if self.params['gradient'] else 'Off'}", custom_id="toggle_gradient", style=discord.ButtonStyle.primary)
        self.gradient_button.callback = self.toggle_gradient
        self.add_item(self.gradient_button)

        self.grain_button = Button(label=f"Grain: {'On' if self.params['grain'] else 'Off'}", custom_id="toggle_grain", style=discord.ButtonStyle.primary)
        self.grain_button.callback = self.toggle_grain
        self.add_item(self.grain_button)

    async def pattern_changed(self, interaction: discord.Interaction):
        self.params['pattern'] = self.pattern_select.values[0]
        await self.update_image(interaction)

    async def aspect_changed(self, interaction: discord.Interaction):
        self.params['aspect_ratio'] = self.aspect_select.values[0]
        await self.update_image(interaction)

    async def font_changed(self, interaction: discord.Interaction):
        self.params['font'] = self.font_select.values[0]
        await self.update_image(interaction)

    async def toggle_glow(self, interaction: discord.Interaction):
        self.params['glow'] = not self.params['glow']
        self.glow_button.label = f"Glow: {'On' if self.params['glow'] else 'Off'}"
        await self.update_image(interaction)

    async def toggle_gradient(self, interaction: discord.Interaction):
        self.params['gradient'] = not self.params['gradient']
        self.gradient_button.label = f"Gradient: {'On' if self.params['gradient'] else 'Off'}"
        await self.update_image(interaction)

    async def toggle_grain(self, interaction: discord.Interaction):
        self.params['grain'] = not self.params['grain']
        self.grain_button.label = f"Grain: {'On' if self.params['grain'] else 'Off'}"
        await self.update_image(interaction)

    async def update_image(self, interaction: discord.Interaction):
        global is_rendering
        if is_rendering:
            await interaction.response.send_message("Please wait, still rendering.", ephemeral=True)
            return
        is_rendering = True
        try:
            img = generate_noise_image(self.params)
            filename = 'noise.png'
            img.save(filename)
            file = discord.File(filename)
            embed_color = discord.Color.from_rgb(*tuple(random.randint(25, 230) for _ in range(3)))
            embed = discord.Embed(title="Updated Noise", color=embed_color)
            embed.set_image(url=f"attachment://{filename}")
            await interaction.response.edit_message(file=file, embed=embed, view=self)
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)
        finally:
            is_rendering = False

class DrawNoiseInput(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="draw_noise_input", description="Draw a beautiful image with noise patterns and real-time controls")
    async def draw_noise_input(self, ctx: discord.ApplicationContext,
        font: discord.Option(str, description="Select a font for text.", choices=fonts) = "Roboto-Black",
        text: discord.Option(str, description="Enter text, use '/' to split lines.", required=False) = None,
        pattern: discord.Option(str, description="Choose a noise pattern style.", choices=patterns) = "classic",
        gradient: discord.Option(bool, description="Overlay a vibrant gradient.") = False,
        glow: discord.Option(bool, description="Add glowing effect to text.") = False,
        grain: discord.Option(bool, description="Add retro film grain.") = False,
        aspect_ratio: discord.Option(str, description="Choose the aspect ratio for the image.", choices=aspect_ratios) = "1:1"
    ):
        global is_rendering
        if is_rendering:
            await ctx.respond("Sorry, an image is already being rendered.")
            return
        is_rendering = True
        try:
            params = {
                "font": font,
                "text": text,
                "pattern": pattern,
                "gradient": gradient,
                "glow": glow,
                "grain": grain,
                "aspect_ratio": aspect_ratio
            }
            img = generate_noise_image(params)
            filename = 'noise.png'
            img.save(filename)
            file = discord.File(filename)
            embed_color = discord.Color.from_rgb(*tuple(random.randint(25, 230) for _ in range(3)))
            embed = discord.Embed(title="Here's your image.", color=embed_color)
            embed.set_image(url=f"attachment://{filename}")
            view = NoiseControls(params)
            await ctx.respond(file=file, embed=embed, view=view)
        except Exception as e:
            await ctx.respond(f"An error occurred: {e}")
        finally:
            is_rendering = False

def setup(bot):
    bot.add_cog(DrawNoiseInput(bot))