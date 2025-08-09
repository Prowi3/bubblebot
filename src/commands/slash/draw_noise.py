import discord, numpy as np, random, math, io
from noise import pnoise2
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
from concurrent.futures import ThreadPoolExecutor

# Adjustable font list (make sure these ttf files exist in your bot files)
FONTS = ['Roboto-Black', 'SpaceMono-Regular', 'SpaceMono-Bold', 'Rubik-Bold', 'Arial-Black']
FONT_DIR = "miscellaneous/Fonts"  # adjust to your path

# Global render lock
is_rendering = False

# Small helper: load font (cached)
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

# Color palettes
PALETTES = {
    "random": None,
    "sunset": [(8, 6, 40), (240, 92, 64), (255, 190, 88)],
    "ocean": [(2, 24, 84), (12, 122, 176), (152, 216, 212)],
    "mono": [(30, 30, 30), (220, 220, 220)],
    "neon": [(10, 255, 200), (255, 10, 200), (200, 10, 255)],
}

# Blend helpers
def blend_add(base, layer, strength=1.0):
    return np.clip(base + layer * strength, 0, 255)

def blend_multiply(base, layer):
    return np.clip((base.astype(np.float32) / 255.0) * (layer.astype(np.float32) / 255.0) * 255.0, 0, 255)

def blend_overlay(base, layer):
    # approximate overlay
    base_f = base.astype(np.float32) / 255.0
    layer_f = layer.astype(np.float32) / 255.0
    mask = base_f <= 0.5
    out = np.empty_like(base_f)
    out[mask] = 2 * base_f[mask] * layer_f[mask]
    out[~mask] = 1 - 2 * (1 - base_f[~mask]) * (1 - layer_f[~mask])
    return np.clip(out * 255.0, 0, 255)

def blend_soft_light(base, layer):
    # approximation for soft light
    base_f = base.astype(np.float32) / 255.0
    layer_f = layer.astype(np.float32) / 255.0
    out = (1 - 2 * layer_f) * (base_f ** 2) + 2 * layer_f * base_f
    return np.clip(out * 255.0, 0, 255)

BLEND_MODES = {
    "add": blend_add,
    "multiply": blend_multiply,
    "overlay": blend_overlay,
    "soft_light": blend_soft_light,
}

# Generate a single perlin noise row (used in threadpool)
def _perlin_row(y, w, scale, ox, oy, octaves, persistence, lacunarity, repeatx, repeaty, base_seed):
    row = np.empty(w, dtype=np.float32)
    yy = (y + oy) / scale
    for x in range(w):
        xx = (x + ox) / scale
        # pnoise2 returns in [-1,1]
        row[x] = pnoise2(xx, yy,
                         octaves=octaves,
                         persistence=persistence,
                         lacunarity=lacunarity,
                         repeatx=repeatx,
                         repeaty=repeaty,
                         base=base_seed)
    return row

# Generate a full perlin grid using threads (returns numpy float32 grid in [-1,1])
def generate_perlin_grid(w, h, scale, ox, oy, octaves, persistence, lacunarity, repeatx, repeaty, base_seed, workers=8):
    grid = np.empty((h, w), dtype=np.float32)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(_perlin_row, y, w, scale, ox, oy, octaves, persistence, lacunarity, repeatx, repeaty, base_seed)
                   for y in range(h)]
        for y, fut in enumerate(futures):
            grid[y, :] = fut.result()
    return grid

# Fast Voronoi by computing at low-res then upscaling
def generate_voronoi(w, h, cells=30, low_res_factor=0.25, seed=None):
    if seed is not None:
        rnd = random.Random(seed)
    else:
        rnd = random
    lw = max(16, int(w * low_res_factor))
    lh = max(16, int(h * low_res_factor))
    # generate random points in low-res space
    pts = [(rnd.randint(0, lw - 1), rnd.randint(0, lh - 1)) for _ in range(cells)]
    dmap = np.full((lh, lw), 1e9, dtype=np.float32)
    for px, py in pts:
        # compute squared distance to (px,py)
        xs = np.arange(lw, dtype=np.float32)
        ys = np.arange(lh, dtype=np.float32)
        xv, yv = np.meshgrid(xs, ys)
        dist = (xv - px) ** 2 + (yv - py) ** 2
        dmap = np.minimum(dmap, dist)
    # normalize and invert for nicer look
    dmap = np.sqrt(dmap)
    dmap = (dmap - dmap.min()) / max(1e-9, (dmap.max() - dmap.min()))
    # invert so cells are bright centers
    dmap = 1.0 - dmap
    # upscale to full
    img = Image.fromarray((dmap * 255).astype(np.uint8))
    img = img.resize((w, h), Image.BICUBIC)
    arr = np.asarray(img).astype(np.float32) / 255.0
    # expand to [-1,1]
    return arr * 2.0 - 1.0

class DrawNoise(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="draw_noise", description='Draw an image using Noise (advanced).')
    async def draw_noise(self, ctx: discord.ApplicationContext,
                         pattern: discord.Option(str, description="Pattern type", choices=["fractal", "ridged", "turbulence", "marble", "radial", "voronoi"]) = "fractal",
                         palette: discord.Option(str, description="Color palette", choices=list(PALETTES.keys())) = "sunset",
                         seed: discord.Option(int, description="Random seed (0 for random)") = 0,
                         size: discord.Option(int, description="Square size px", choices=[512, 768, 1080, 1536]) = 1080,
                         scale: discord.Option(float, description="Noise scale (bigger = larger blobs)") = 300.0,
                         octaves: discord.Option(int, description="Octaves") = 3,
                         lacunarity: discord.Option(float, description="Lacunarity") = 2.0,
                         persistence: discord.Option(float, description="Persistence") = 0.5,
                         color_strength: discord.Option(float, description="Color strength (0..2)") = 1.0,
                         layers: discord.Option(int, description="Noise layers to stack (0 = single)") = 1,
                         blend_mode: discord.Option(str, description="Blend mode for layers", choices=list(BLEND_MODES.keys())) = "soft_light",
                         mirror: discord.Option(bool, description="Mirror horizontally") = False,
                         symmetry: discord.Option(bool, description="Vertical symmetry") = False,
                         text: discord.Option(str, description="Optional text (use / for newline)") = None,
                         font: discord.Option(str, description="Font", choices=FONTS) = "Roboto-Black",
                         outline: discord.Option(bool, description="Text outline") = True
                         ):
        global is_rendering
        if is_rendering:
            await ctx.respond("Sorry — another render is running. Try again in a moment.")
            return
        is_rendering = True
        await ctx.defer()  # give user a moment; rendering may take time
        try:
            w = h = size
            # seed handling
            if seed == 0:
                seed = random.randint(0, 2**31 - 1)
            rnd = random.Random(seed)
            base_color = None
            palette_values = PALETTES.get(palette)
            if palette_values is None:
                # random palette
                palette_values = [tuple(rnd.randint(0, 255) for _ in range(3)) for _ in range(3)]
            # Prepare initial base array (floating)
            base = np.zeros((h, w, 3), dtype=np.float32)

            # helper to map normalized [-1,1] noise to palette color
            def map_to_palette(noise_grid):  # noise_grid in [-1,1]
                # Normalize to 0..1
                n = (noise_grid + 1.0) / 2.0
                # map to palette by linear interpolation across palette stops
                stops = len(palette_values) - 1
                scaled = n * stops
                idx = np.clip(scaled.astype(int), 0, stops - 1)
                frac = scaled - idx
                out = np.empty((h, w, 3), dtype=np.float32)
                for i in range(stops):
                    mask = (idx == i)
                    if mask.any():
                        c0 = np.array(palette_values[i], dtype=np.float32)
                        c1 = np.array(palette_values[i + 1], dtype=np.float32)
                        out[mask] = c0 + (c1 - c0) * frac[mask][:, None]
                # if any values exactly equal to max stop:
                mask_end = (idx == stops)
                if mask_end.any():
                    out[mask_end] = np.array(palette_values[-1], dtype=np.float32)
                return out

            # generate layers
            blend_fn = BLEND_MODES.get(blend_mode, blend_soft_light)
            current = base.copy()

            # prepare repeated generation settings
            repeat = 1024

            for li in range(max(1, layers)):
                # vary scale / seeds per layer for interest
                layer_scale = scale * (1.0 + (li * 0.6))
                layer_seed = seed + li * 97
                ox = rnd.uniform(0, 10000)
                oy = rnd.uniform(0, 10000)

                if pattern == "fractal":
                    grid = generate_perlin_grid(w, h, layer_scale, ox, oy, octaves, persistence, lacunarity, repeat, repeat, layer_seed, workers=8)
                elif pattern == "ridged":
                    # ridged: 1 - abs(noise)
                    g = generate_perlin_grid(w, h, layer_scale, ox, oy, octaves, persistence, lacunarity, repeat, repeat, layer_seed, workers=8)
                    grid = 1.0 - np.abs(g)
                    grid = grid * 2.0 - 1.0
                elif pattern == "turbulence":
                    # turbulence = sum(abs(noise * freq))
                    t = np.zeros((h, w), dtype=np.float32)
                    freq = 1.0
                    amp = 1.0
                    for o in range(octaves):
                        g = generate_perlin_grid(w, h, layer_scale / freq, ox * freq, oy * freq, 1, persistence, lacunarity, repeat, repeat, layer_seed + o, workers=6)
                        t += np.abs(g) * amp
                        amp *= persistence
                        freq *= lacunarity
                    # normalize roughly to [-1,1]
                    t = t / t.max()
                    grid = t * 2.0 - 1.0
                elif pattern == "marble":
                    g = generate_perlin_grid(w, h, layer_scale, ox, oy, octaves, persistence, lacunarity, repeat, repeat, layer_seed, workers=8)
                    # marble = sin(x + noise*freq)
                    xs = np.linspace(0, math.pi * 6, w)
                    xv = np.tile(xs, (h, 1))
                    grid = np.sin((xv / (w / 8.0)) + g * 4.0)
                elif pattern == "radial":
                    # radial gradient with noise add
                    cx, cy = w / 2.0, h / 2.0
                    xs = np.arange(w, dtype=np.float32) - cx
                    ys = np.arange(h, dtype=np.float32) - cy
                    xv, yv = np.meshgrid(xs, ys)
                    rmap = np.sqrt(xv ** 2 + yv ** 2)
                    rnorm = (rmap - rmap.min()) / (rmap.max() - rmap.min())
                    g = generate_perlin_grid(w, h, layer_scale, ox, oy, octaves, persistence, lacunarity, repeat, repeat, layer_seed, workers=6)
                    grid = 1.0 - rnorm + 0.25 * g
                    grid = (grid - grid.min()) / (grid.max() - grid.min()) * 2.0 - 1.0
                elif pattern == "voronoi":
                    grid = generate_voronoi(w, h, cells=40 + li * 10, low_res_factor=0.18, seed=layer_seed)
                else:
                    grid = generate_perlin_grid(w, h, layer_scale, ox, oy, octaves, persistence, lacunarity, repeat, repeat, layer_seed, workers=6)

                # optionally mirror / symmetry to make patterns cooler
                if mirror:
                    grid = np.concatenate([grid, grid[:, ::-1]], axis=1)[:, :w]
                if symmetry:
                    top = grid[:h//2, :]
                    grid = np.vstack([top, top[::-1, :]])

                # map to palette (rgb floats)
                layer_rgb = map_to_palette(grid) * color_strength

                # blend into current
                current = blend_fn(current, layer_rgb)

            # final post-processing: normalize and convert to uint8
            final = np.clip(current, 0, 255).astype(np.uint8)

            # Convert to PIL image
            img = Image.fromarray(final, mode='RGB')

            # optional artistic finishing passes
            img = img.filter(ImageFilter.GaussianBlur(radius=0.3))  # subtle smooth

            # Text rendering
            if text:
                lines = text.split('/')
                # estimate font size adaptively
                # attempt to find largest font size that fits
                font_size = max(18, int(min(w, h) / (1 + 0.5 * len("".join(lines)))))
                fnt = load_font(font, font_size)
                draw = ImageDraw.Draw(img)
                # if text too large, reduce until fits
                while True:
                    bbox_heights = []
                    bbox_width = 0
                    for ln in lines:
                        b = fnt.getbbox(ln)
                        bbox_width = max(bbox_width, b[2] - b[0])
                        bbox_heights.append(b[3] - b[1])
                    total_h = sum(bbox_heights) + (len(lines)-1) * 6
                    if (bbox_width < w * 0.9 and total_h < h * 0.9) or font_size < 12:
                        break
                    font_size = int(font_size * 0.9)
                    fnt = load_font(font, font_size)
                # compute starting y
                y = (h - total_h) // 2
                for ln in lines:
                    b = fnt.getbbox(ln)
                    tw = b[2] - b[0]
                    tx = (w - tw) // 2
                    if outline:
                        outline_color = (0,0,0)
                        for dx, dy in [(-2,-2),(-2,2),(2,-2),(2,2),(-1,0),(1,0),(0,-1),(0,1)]:
                            draw.text((tx+dx, y+dy - b[1]), ln, font=fnt, fill=outline_color)
                    draw.text((tx, y - b[1]), ln, font=fnt, fill=(255,255,255))
                    y += (b[3] - b[1]) + 6

            # Save to BytesIO and send
            bio = io.BytesIO()
            img.save(bio, format="PNG", optimize=True)
            bio.seek(0)
            discord_file = discord.File(fp=bio, filename="noise.png")
            embed = discord.Embed(title="Here's your image.", color=discord.Color.from_rgb(*[int(c) for c in (palette_values[0])]))
            embed.set_image(url="attachment://noise.png")
            await ctx.respond(file=discord_file, embed=embed)

        except Exception as e:
            await ctx.respond(f"An error occurred while rendering: `{e}`")
        finally:
            is_rendering = False

def setup(bot):
    bot.add_cog(DrawNoise(bot))