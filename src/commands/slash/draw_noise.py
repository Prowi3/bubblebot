import discord, numpy as np, random, math
from noise import pnoise2
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageChops

fonts = ['Roboto-Black', 'SpaceMono-Regular', 'SpaceMono-Bold', 'Rubik-Bold', 'Arial-Black']
is_rendering = False

class DrawNoise(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.slash_command(name="draw_noise", description='Draw an image using Noise')
    async def draw_noise(self, ctx: discord.ApplicationContext,
        font: discord.Option(str, description="Select a font.", choices=fonts) = "Roboto-Black",
        text: discord.Option(str = '', description="Enter your text here. Use '/' to split lines.") = None,
        octaves: discord.Option(int, description="Choose octave amount") = 1,
        lacunarity: discord.Option(float, description="Choose lacunarity") = 5.0,
        persistence: discord.Option(float, description="Choose persistence") = 0.5
    ):
        global is_rendering
        if is_rendering:
            await ctx.send("Sorry, an image is already being rendered.")
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

            noise = np.vectorize(pnoise2)(xx / scale, yy / scale,
                octaves=octaves, persistence=persistence,
                lacunarity=lacunarity, repeatx=1024, repeaty=1024, base=1)

            r = np.clip(color[0] + noise * 100, 0, 255).astype(np.uint8)
            g = np.clip(color[1] + noise * 100, 0, 255).astype(np.uint8)
            b = np.clip(color[2] + noise * 100, 0, 255).astype(np.uint8)
            img = Image.fromarray(np.stack([r, g, b], -1))

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
                for i, line in enumerate(lines):
                    bbox = fnt.getbbox(line)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                    tx = (w - tw) // 2
                    tdraw.text((tx, ty - bbox[1]), line, fill=(255, 255, 255), font=fnt)
                    ty += th
                img = ImageChops.soft_light(img, txt)

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

def setup(bot): bot.add_cog(DrawNoise(bot))