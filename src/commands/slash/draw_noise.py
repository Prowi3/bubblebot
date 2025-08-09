import os, io, random, math
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    from opensimplex import OpenSimplex
    _HAS_OSIMPLEX = True
except Exception:
    _HAS_OSIMPLEX = False
try:
    from noise import pnoise2
    _HAS_NOISE = True
except Exception:
    _HAS_NOISE = False

FONTS = ['Roboto-Black', 'SpaceMono-Regular', 'SpaceMono-Bold', 'Rubik-Bold', 'Arial-Black']
FONT_DIR = "miscellaneous/Fonts"
is_rendering = False
_font_cache = {}

def load_font(name: str, size: int):
    key = (name, size)
    if key in _font_cache:
        return _font_cache[key]
    try:
        fp = f"{FONT_DIR}/{name}.ttf"
        f = ImageFont.truetype(fp, size)
    except Exception:
        f = ImageFont.load_default()
    _font_cache[key] = f
    return f

PALETTES = {
    "random": None,
    "sunset": [(8, 6, 40), (240, 92, 64), (255, 190, 88)],
    "ocean": [(2, 24, 84), (12, 122, 176), (152, 216, 212)],
    "mono": [(30, 30, 30), (220, 220, 220)],
    "neon": [(10, 255, 200), (255, 10, 200), (200, 10, 255)],
}

def lerp(a, b, t):
    return a + (b - a) * t

def map_to_palette_value(val, palette):
    t = (val + 1.0) / 2.0
    stops = len(palette) - 1
    scaled = t * stops
    i = int(math.floor(scaled))
    i = max(0, min(i, stops - 1))
    frac = scaled - i
    c0 = palette[i]
    c1 = palette[i + 1]
    return (int(lerp(c0[0], c1[0], frac)),
            int(lerp(c0[1], c1[1], frac)),
            int(lerp(c0[2], c1[2], frac)))

def perlin_noise(x, y, scale, octaves, persistence, lacunarity, base_seed, use_simplex=None):
    if use_simplex is None:
        use_simplex = _HAS_OSIMPLEX and not _HAS_NOISE
    val = 0.0
    amplitude = 1.0
    frequency = 1.0
    if use_simplex:
        if not hasattr(perlin_noise, "_osimplex_instances"):
            perlin_noise._osimplex_instances = {}
        key = base_seed
        if key not in perlin_noise._osimplex_instances:
            perlin_noise._osimplex_instances[key] = OpenSimplex(seed=base_seed)
        s = perlin_noise._osimplex_instances[key]
        for o in range(octaves):
            val += s.noise2d(x * frequency / scale, y * frequency / scale) * amplitude
            amplitude *= persistence
            frequency *= lacunarity
    else:
        if not _HAS_NOISE:
            raise RuntimeError("No suitable noise backend available. Install 'opensimplex' or 'noise'.")
        for o in range(octaves):
            val += pnoise2(x * frequency / scale, y * frequency / scale,
                           octaves=1,
                           persistence=persistence,
                           lacunarity=lacunarity,
                           repeatx=1024, repeaty=1024, base=base_seed + o) * amplitude
            amplitude *= persistence
            frequency *= lacunarity
    return max(-1.0, min(1.0, val))

class DrawNoise(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="draw_noise", description='Draw an image using Noise (stable low-memory).')
    async def draw_noise(self, ctx: discord.ApplicationContext,
                         pattern: discord.Option(str, choices=["fractal", "ridged", "turbulence", "marble", "radial", "voronoi"]) = "fractal",
                         palette: discord.Option(str, choices=list(PALETTES.keys())) = "sunset",
                         seed: discord.Option(int) = 0,
                         size: discord.Option(int, choices=[256, 384, 512]) = 512,
                         scale: discord.Option(float) = 200.0,
                         octaves: discord.Option(int) = 3,
                         lacunarity: discord.Option(float) = 2.0,
                         persistence: discord.Option(float) = 0.5,
                         color_strength: discord.Option(float) = 1.0,
                         layers: discord.Option(int) = 1,
                         mirror: discord.Option(bool) = False,
                         symmetry: discord.Option(bool) = False,
                         low_memory: discord.Option(bool) = True,
                         text: discord.Option(str) = None,
                         font: discord.Option(str, choices=FONTS) = "Roboto-Black",
                         outline: discord.Option(bool) = True):
        global is_rendering
        if is_rendering:
            await ctx.respond("Another render is running.")
            return
        is_rendering = True
        await ctx.defer()
        try:
            if seed == 0:
                seed = random.randint(0, 2**31 - 1)
            rnd = random.Random(seed)
            use_simplex_env = os.getenv("USE_OPENSIMPLEX", "").lower() in ("1", "true", "yes")
            use_simplex = (_HAS_OSIMPLEX and (use_simplex_env or not _HAS_NOISE)) or (_HAS_OSIMPLEX and _HAS_NOISE and use_simplex_env)
            if not (_HAS_NOISE or _HAS_OSIMPLEX):
                await ctx.respond("Install either 'noise' or 'opensimplex' in the environment.")
                return
            palette_values = PALETTES.get(palette)
            if palette_values is None:
                palette_values = [tuple(rnd.randint(0, 255) for _ in range(3)) for _ in range(3)]
            w = h = max(64, min(1024, int(size)))
            tile = 64 if low_memory else 128
            img = Image.new("RGB", (w, h))
            pixels = img.load()
            repeat = 1024
            for ly in range(layers):
                layer_scale = scale * (1.0 + ly * 0.6)
                layer_seed = seed + ly * 97
                ox = rnd.uniform(0, 10000)
                oy = rnd.uniform(0, 10000)
                for ty in range(0, h, tile):
                    for tx in range(0, w, tile):
                        for yy in range(ty, min(h, ty + tile)):
                            for xx in range(tx, min(w, tx + tile)):
                                nx = xx + ox
                                ny = yy + oy
                                if pattern == "fractal":
                                    v = perlin_noise(nx, ny, layer_scale, octaves, persistence, lacunarity, layer_seed, use_simplex=use_simplex)
                                elif pattern == "ridged":
                                    g = perlin_noise(nx, ny, layer_scale, octaves, persistence, lacunarity, layer_seed, use_simplex=use_simplex)
                                    v = 1.0 - abs(g)
                                    v = v * 2.0 - 1.0
                                elif pattern == "turbulence":
                                    t = 0.0
                                    freq = 1.0
                                    amp = 1.0
                                    for o in range(octaves):
                                        t += abs(perlin_noise(nx * freq, ny * freq, layer_scale, 1, persistence, lacunarity, layer_seed + o, use_simplex=use_simplex)) * amp
                                        amp *= persistence
                                        freq *= lacunarity
                                    v = (t / max(1e-9, t)) * 2.0 - 1.0 if t != 0 else 0.0
                                elif pattern == "marble":
                                    g = perlin_noise(nx, ny, layer_scale, octaves, persistence, lacunarity, layer_seed, use_simplex=use_simplex)
                                    v = math.sin((xx / max(1.0, (w / 8.0))) + g * 4.0)
                                elif pattern == "radial":
                                    cx, cy = w / 2.0, h / 2.0
                                    rx = xx - cx
                                    ry = yy - cy
                                    rmap = math.sqrt(rx * rx + ry * ry)
                                    rnorm = (rmap - 0) / max(1.0, (math.sqrt((cx**2)+(cy**2))))
                                    g = perlin_noise(nx, ny, layer_scale, octaves, persistence, lacunarity, layer_seed, use_simplex=use_simplex)
                                    v = 1.0 - rnorm + 0.25 * g
                                    v = max(-1.0, min(1.0, (v - (-1.0)) / (2.0) * 2.0 - 1.0))
                                else:
                                    v = perlin_noise(nx, ny, layer_scale, octaves, persistence, lacunarity, layer_seed, use_simplex=use_simplex)
                                col = map_to_palette_value(v, palette_values)
                                if ly == 0:
                                    pixels[xx, yy] = col
                                else:
                                    prev = pixels[xx, yy]
                                    blended = (int((prev[0] + col[0]) * 0.5 * color_strength),
                                               int((prev[1] + col[1]) * 0.5 * color_strength),
                                               int((prev[2] + col[2]) * 0.5 * color_strength))
                                    pixels[xx, yy] = blended
            if mirror:
                img = Image.frombytes("RGB", img.size, img.tobytes()) 
                img = Image.merge("RGB", [Image.frombytes("L", img.size, img.getchannel(c).tobytes()).transpose(Image.FLIP_LEFT_RIGHT) for c in img.getbands()]).transpose(Image.FLIP_LEFT_RIGHT)
            if symmetry:
                left = img.crop((0,0,w//2,h))
                right = left.transpose(Image.FLIP_LEFT_RIGHT)
                img.paste(left, (0,0))
                img.paste(right, (w - left.width, 0))
            img = img.filter(ImageFilter.GaussianBlur(radius=0.4))
            if text:
                lines = text.split('/')
                font_size = max(10, int(min(w, h) / (1 + 0.4 * len("".join(lines)))))
                fnt = load_font(font, font_size)
                draw = ImageDraw.Draw(img)
                while True:
                    bbox_heights = []
                    bbox_width = 0
                    for ln in lines:
                        b = fnt.getbbox(ln)
                        bbox_width = max(bbox_width, b[2] - b[0])
                        bbox_heights.append(b[3] - b[1])
                    total_h = sum(bbox_heights) + (len(lines)-1) * 4
                    if (bbox_width < w * 0.9 and total_h < h * 0.9) or font_size < 10:
                        break
                    font_size = int(font_size * 0.9)
                    fnt = load_font(font, font_size)
                y = (h - total_h) // 2
                for ln in lines:
                    b = fnt.getbbox(ln)
                    tw = b[2] - b[0]
                    tx = (w - tw) // 2
                    if outline:
                        for dx, dy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                            draw.text((tx+dx, y+dy - b[1]), ln, font=fnt, fill=(0,0,0))
                    draw.text((tx, y - b[1]), ln, font=fnt, fill=(255,255,255))
                    y += (b[3] - b[1]) + 4
            bio = io.BytesIO()
            img.save(bio, format="PNG", optimize=True)
            bio.seek(0)
            discord_file = discord.File(fp=bio, filename="noise.png")
            embed = discord.Embed(title="Here's your image.", color=discord.Color.from_rgb(*palette_values[0]))
            embed.set_image(url="attachment://noise.png")
            await ctx.respond(file=discord_file, embed=embed)
        except Exception as e:
            await ctx.respond(f"Rendering error: `{e}`")
        finally:
            is_rendering = False

def setup(bot):
    bot.add_cog(DrawNoise(bot))