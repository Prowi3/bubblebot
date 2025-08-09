import discord, numpy as np, random, math
from noise import pnoise2
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

fonts = ['Roboto-Black', 'SpaceMono-Regular', 'SpaceMono-Bold', 'Rubik-Bold', 'Arial-Black']
patterns = ['classic', 'swirl', 'ripple', 'concentric', 'marble']
is_rendering = False

class DrawNoise(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot

    @commands.slash_command(name="draw_noise", description='Draw a beautiful image with noise patterns and effects')
    async def draw_noise(self, ctx: discord.ApplicationContext,
        font: discord.Option(str, description="Select a font for text.", choices=fonts) = "Roboto-Black",
        text: discord.Option(str, description="Enter text, use '/' to split lines.", required=False) = None,
        octaves: discord.Option(int, description="Noise detail level. Higher = more complexity.") = 1,
        lacunarity: discord.Option(float, description="Controls frequency of detail in noise.") = 5.0,
        persistence: discord.Option(float, description="Controls amplitude falloff of noise.") = 0.5,
        pattern: discord.Option(str, description="Choose a noise pattern style.", choices=patterns) = "classic",
        gradient: discord.Option(bool, description="Overlay a vibrant gradient.") = False,
        glow: discord.Option(bool, description="Add glowing effect to text.") = False,
        grain: discord.Option(bool, description="Add retro film grain.") = False,
        vignette: discord.Option(bool, description="Darken edges for depth.") = False
    ):
        global is_rendering
        if is_rendering:
            await ctx.respond("Sorry, an image is already being rendered.")
            return
        is_rendering = True
        try:
            w, h = 1080, 1080
            base = Image.new('RGB', (w, h))
            scale = 300.0
            color = tuple(random.randint(0, 255) for _ in range(3))
            ox, oy = random.uniform(0, 1000), random.uniform(0, 1000)

            xs = np.arange(w) + ox
            ys = np.arange(h) + oy
            xx, yy = np.meshgrid(xs, ys)

            if pattern == "swirl":
                angle = np.sqrt(xx**2 + yy**2) / 50
                xx, yy = xx + np.sin(angle) * 20, yy + np.cos(angle) * 20
            elif pattern == "ripple":
                xx += np.sin(yy / 20) * 10
                yy += np.sin(xx / 20) * 10
            elif pattern == "concentric":
                dist = np.sqrt((xx - w/2)**2 + (yy - h/2)**2)
                xx += np.sin(dist / 15) * 15
                yy += np.cos(dist / 15) * 15
            elif pattern == "marble":
                xx += np.sin(xx / 30) * 40

            noise = np.vectorize(pnoise2)(xx / scale, yy / scale,
                octaves=octaves, persistence=persistence,
                lacunarity=lacunarity, repeatx=1024, repeaty=1024, base=1)

            r = np.clip(color[0] + noise * 100, 0, 255).astype(np.uint8)
            g = np.clip(color[1] + noise * 100, 0, 255).astype(np.uint8)
            b = np.clip(color[2] + noise * 100, 0, 255).astype(np.uint8)
            img = Image.fromarray(np.stack([r, g, b], -1))

            if gradient:
                grad = Image.new("RGB", (w, h))
                grad_draw = ImageDraw.Draw(grad)
                c1 = tuple(random.randint(0, 255) for _ in range(3))
                c2 = tuple(random.randint(0, 255) for _ in range(3))
                for y in range(h):
                    blend = y / h
                    grad_color = tuple(int(c1[i] * (1 - blend) + c2[i] * blend) for i in range(3))
                    grad_draw.line([(0, y), (w, y)], fill=grad_color)
                img = ImageChops.overlay(img, grad)

            if text:
                font_size = int(math.sqrt(w * h) / len(text)) + 25
                font_path = f"miscellaneous/Fonts/{font}.ttf"
                fnt = ImageFont.truetype(font_path, font_size)
                txt = Image.new('RGB', (w, h))
                tdraw = ImageDraw.Draw(txt)
                lines = text.split('/')
                bboxes = [fnt.getbbox(l) for l in lines]
                heights = [b[3] - b[1] for b in bboxes]
                ty = (h - sum(heights)) // 2
                for line in lines:
                    bbox = fnt.getbbox(line)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                    tx = (w - tw) // 2
                    if glow:
                        glow_layer = Image.new("RGB", (w, h), (0, 0, 0))
                        glow_draw = ImageDraw.Draw(glow_layer)
                        glow_draw.text((tx, ty - bbox[1]), line, font=fnt, fill=color)
                        for _ in range(3):
                            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(5))
                        img = ImageChops.screen(img, glow_layer)
                    tdraw.text((tx, ty - bbox[1]), line, fill=(255, 255, 255), font=fnt)
                    ty += th
                img = ImageChops.soft_light(img, txt)

            if grain:
                grain_layer = np.random.randint(0, 50, (h, w, 3), dtype=np.uint8)
                img = ImageChops.add(img, Image.fromarray(grain_layer))

            if vignette:
                vignette_layer = Image.new('L', (w, h), 0)
                grad_draw = ImageDraw.Draw(vignette_layer)
                for i in range(max(w, h)//2, 0, -1):
                    alpha = int(255 * (1 - i / (max(w, h)//2)))
                    grad_draw.ellipse((w/2 - i, h/2 - i, w/2 + i, h/2 + i), fill=alpha)
                vignette_layer = vignette_layer.filter(ImageFilter.GaussianBlur(100))
                img.putalpha(vignette_layer)
                img = img.convert("RGB")

            embed_color = discord.Color.from_rgb(*color)
            img.save('gradient.png')
            file = discord.File('gradient.png')
            embed = discord.Embed(title="Here's your image.", color=embed_color)
            embed.set_image(url="attachment://gradient.png")
            await ctx.respond(file=file, embed=embed)

        except Exception as e:
            await ctx.respond(f"An error occurred: {str(e)}")
        finally:
            is_rendering = False

def setup(bot): 
    bot.add_cog(DrawNoise(bot))