import discord, numpy as np, random, math
from noise import pnoise2
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

fonts = ['Roboto-Black', 'SpaceMono-Regular', 'SpaceMono-Bold', 'Rubik-Bold', 'Arial-Black']
patterns = ['classic', 'swirl', 'ripple', 'concentric', 'marble', 'voronoi', 'turbulence', 'waves']
aspect_ratios = ["1:1", "16:9", "4:3", "9:16", "21:9"]
is_rendering = False

DEFAULT_OCTAVES = 3
DEFAULT_LACUNARITY = 2.0
DEFAULT_PERSISTENCE = 0.5

class DrawNoise(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="draw_noise", description='Draw a beautiful image with noise patterns and effects')
    async def draw_noise(self, ctx: discord.ApplicationContext,
        font: discord.Option(str, description="Select a font for text.", choices=fonts) = "Roboto-Black",
        text: discord.Option(str, description="Enter text, use '/' to split lines.", required=False) = None,
        pattern: discord.Option(str, description="Choose a noise pattern style.", choices=patterns) = "classic",
        gradient: discord.Option(bool, description="Overlay a vibrant gradient.") = False,
        glow: discord.Option(bool, description="Add glowing effect to text.") = False,
        grain: discord.Option(bool, description="Add retro film grain.") = False,
        aspect_ratio: discord.Option(str, description="Choose the aspect ratio for the image.", choices=aspect_ratios) = "1:1",
        gif: discord.Option(bool, description="Return a GIF animation (noise will animate).") = False,
        frames: discord.Option(int, description="Number of frames for the GIF (if gif=true).", required=False) = 12,
        fps: discord.Option(int, description="Frames per second for the GIF (if gif=true).", required=False) = 12
    ):
        global is_rendering
        if is_rendering:
            await ctx.respond("Sorry, an image is already being rendered.")
            return
        is_rendering = True
        try:
            ratio_w, ratio_h = map(int, aspect_ratio.split(":"))
            max_size = 1080
            if ratio_w >= ratio_h:
                w = max_size
                h = int(max_size * (ratio_h / ratio_w))
            else:
                h = max_size
                w = int(max_size * (ratio_w / ratio_h))
            base_scale = random.uniform(180.0, 380.0)
            base_color = tuple(random.randint(25, 230) for _ in range(3))
            base_ox, base_oy = random.uniform(0, 2000), random.uniform(0, 2000)
            shift_x = random.uniform(-12.0, 12.0)
            shift_y = random.uniform(-12.0, 12.0)
            xs = np.arange(w, dtype=np.float32) - (w / 2)
            ys = np.arange(h, dtype=np.float32) - (h / 2)
            base_xx, base_yy = np.meshgrid(xs, ys)
            def perlin_grid(xarr, yarr):
                flat_x = xarr.ravel()
                flat_y = yarr.ravel()
                vals = [pnoise2(float(a), float(b),
                                octaves=DEFAULT_OCTAVES,
                                persistence=DEFAULT_PERSISTENCE,
                                lacunarity=DEFAULT_LACUNARITY,
                                repeatx=4096, repeaty=4096, base=0)
                        for a, b in zip(flat_x, flat_y)]
                return np.array(vals, dtype=np.float32).reshape(xarr.shape)
            def apply_pattern(xx, yy, pattern_name):
                if pattern_name == "swirl":
                    r = np.sqrt(xx**2 + yy**2) + 1e-6
                    theta = np.arctan2(yy, xx)
                    twist = 0.8 + random.uniform(0.0, 1.2)
                    theta = theta + twist * (r / max(w, h)) * 6.0
                    xx2 = r * np.cos(theta)
                    yy2 = r * np.sin(theta)
                    xx2 += np.sin(yy2 / 15.0) * 8.0
                    yy2 += np.cos(xx2 / 15.0) * 8.0
                    return xx2, yy2
                elif pattern_name == "ripple":
                    xx2 = xx + np.sin(yy / 12.0) * 18.0
                    yy2 = yy + np.sin(xx / 18.0) * 12.0
                    xx2 += np.sin(xx / 40.0 + yy / 60.0) * 6.0
                    return xx2, yy2
                elif pattern_name == "concentric":
                    dist = np.sqrt((xx)**2 + (yy)**2)
                    xx2 = xx + np.sin(dist / 12.0) * 22.0
                    yy2 = yy + np.cos(dist / 12.0) * 22.0
                    return xx2, yy2
                elif pattern_name == "marble":
                    xx2 = xx + np.sin(xx / 28.0) * 48.0
                    yy2 = yy + np.sin(yy / 40.0) * 10.0
                    return xx2, yy2
                elif pattern_name == "voronoi":
                    offsets = []
                    for i in range(6):
                        offsets.append(np.stack([xx + random.uniform(-40, 40), yy + random.uniform(-40, 40)], axis=0))
                    disp = sum(np.sin(o[0] / 30.0) + np.cos(o[1] / 30.0) for o in offsets)
                    return xx + disp * 6.0, yy + disp * 6.0
                elif pattern_name == "turbulence":
                    turb = np.zeros_like(xx)
                    amp = 1.0
                    freq = 1.0
                    for i in range(4):
                        turb += amp * np.sin((xx * freq) / (20.0 + i * 6.0)) * np.cos((yy * freq) / (18.0 + i * 6.0))
                        amp *= 0.5
                        freq *= 2.0
                    return xx + turb * 20.0, yy + (turb * 14.0)
                elif pattern_name == "waves":
                    xx2 = xx + np.sin(yy / 10.0 + np.sin(xx / 60.0)) * 20.0
                    yy2 = yy + np.cos(xx / 14.0 + np.cos(yy / 50.0)) * 10.0
                    return xx2, yy2
                else:
                    return xx, yy
            gradient_img = None
            if gradient:
                grad = Image.new("RGB", (w, h))
                grad_draw = ImageDraw.Draw(grad)
                c1 = tuple(random.randint(0, 255) for _ in range(3))
                c2 = tuple(random.randint(0, 255) for _ in range(3))
                for y in range(h):
                    blend = y / max(1, (h - 1))
                    grad_color = tuple(int(c1[i] * (1 - blend) + c2[i] * blend) for i in range(3))
                    grad_draw.line([(0, y), (w, y)], fill=grad_color)
                gradient_img = grad
            text_layer_rgb = None
            if text:
                lines = text.split('/')
                longest = max(lines, key=len)
                font_size = max(28, int((w / max(1, len(longest))) * 0.9))
                font_path = f"miscellaneous/Fonts/{font}.ttf"
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
                    if glow:
                        glow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                        glow_draw = ImageDraw.Draw(glow_layer)
                        glow_color = tuple(min(255, int(c * 1.4)) for c in base_color) + (180,)
                        glow_draw.text((tx, ty - bbox[1]), line, font=fnt, fill=glow_color)
                        for _ in range(4):
                            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(6))
                        base_for_glow = Image.new('RGBA', (w, h), (0, 0, 0, 0))
                        base_for_glow = Image.alpha_composite(base_for_glow, glow_layer)
                        base_for_glow = Image.alpha_composite(base_for_glow, txt)
                        txt = base_for_glow
                        tdraw = ImageDraw.Draw(txt)
                    tdraw.text((tx, ty - bbox[1]), line, fill=(255, 255, 255, 255), font=fnt)
                    ty += th + 10
                text_layer_rgb = txt.convert('RGB')
            def make_frame(t_frac):
                ox = base_ox + shift_x * (t_frac - 0.5) * 2.0
                oy = base_oy + shift_y * (t_frac - 0.5) * 2.0
                xx = base_xx + ox
                yy = base_yy + oy
                xx_t, yy_t = apply_pattern(xx, yy, pattern)
                noise = perlin_grid(xx_t / base_scale, yy_t / base_scale)
                noise_scaled = (noise - noise.min()) / (noise.max() - noise.min() + 1e-9)
                r = np.clip(base_color[0] + (noise_scaled - 0.5) * 220, 0, 255).astype(np.uint8)
                g = np.clip(base_color[1] + (noise_scaled - 0.5) * 220, 0, 255).astype(np.uint8)
                b = np.clip(base_color[2] + (noise_scaled - 0.5) * 220, 0, 255).astype(np.uint8)
                img = Image.fromarray(np.dstack([r, g, b]), 'RGB')
                if gradient_img is not None:
                    img = ImageChops.overlay(img, gradient_img)
                if text_layer_rgb is not None:
                    img = ImageChops.soft_light(img, text_layer_rgb)
                if grain:
                    grain_layer = np.random.randint(0, 60, (h, w, 3), dtype=np.uint8)
                    img = ImageChops.add(img, Image.fromarray(grain_layer))
                return img
            if gif:
                frames = max(2, min(60, int(frames or 12)))
                fps = max(1, min(60, int(fps or 12)))
                frame_images = []
                for i in range(frames):
                    t_frac = i / float(max(1, frames - 1))
                    frame_img = make_frame(t_frac)
                    frame_images.append(frame_img.convert('P', palette=Image.ADAPTIVE))
                filename = 'noise.gif'
                duration_ms = int(1000.0 / fps)
                frame_images[0].save(
                    filename,
                    save_all=True,
                    append_images=frame_images[1:],
                    duration=duration_ms,
                    loop=0,
                    disposal=2,
                    optimize=False
                )
                file = discord.File(filename)
                embed_color = discord.Color.from_rgb(*base_color)
                embed = discord.Embed(title="Here's your GIF.", color=embed_color)
                embed.set_image(url=f"attachment://{filename}")
                await ctx.respond(file=file, embed=embed)
            else:
                img = make_frame(0.0)
                filename = 'noise.png'
                img.save(filename)
                file = discord.File(filename)
                embed_color = discord.Color.from_rgb(*base_color)
                embed = discord.Embed(title="Here's your image.", color=embed_color)
                embed.set_image(url=f"attachment://{filename}")
                await ctx.respond(file=file, embed=embed)
        except Exception as e:
            await ctx.respond(f"An error occurred: {str(e)}")
        finally:
            is_rendering = False

def setup(bot):
    bot.add_cog(DrawNoise(bot))