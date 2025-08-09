import discord
from discord.ext import commands
from discord.commands import Option
import httpx
import re
from io import BytesIO
from PIL import Image
import numpy as np

MAX_DIM = 1024

modes = [
    "luminance", "hue", "red", "green", "blue",
    "inverted_luminance", "random_noise", "edge_brightness"
]

directions = ["horizontal", "vertical"]

def _resize_keep_aspect(img: Image.Image, max_dim=MAX_DIM):
    w, h = img.size
    if max(w, h) <= max_dim:
        return img
    if w >= h:
        return img.resize((max_dim, int(h * (max_dim / w))), Image.LANCZOS)
    return img.resize((int(w * (max_dim / h)), max_dim), Image.LANCZOS)

def _compute_key_array(arr, mode):
    if mode == "luminance":
        r, g, b = [arr[..., i].astype(np.float32) for i in range(3)]
        return 0.2126*r + 0.7152*g + 0.0722*b
    if mode == "inverted_luminance":
        r, g, b = [arr[..., i].astype(np.float32) for i in range(3)]
        return 255 - (0.2126*r + 0.7152*g + 0.0722*b)
    if mode == "random_noise":
        return np.random.uniform(0, 255, size=arr.shape[0])
    if mode == "edge_brightness":
        lum = 0.2126*arr[...,0] + 0.7152*arr[...,1] + 0.0722*arr[...,2]
        left = np.roll(lum, 1)
        right = np.roll(lum, -1)
        diff = np.abs(left - right)
        return diff.astype(np.float32)
    if mode in ("red", "green", "blue"):
        return arr[..., {"red":0, "green":1, "blue":2}[mode]].astype(np.float32)
    if mode == "hue":
        r = arr[...,0].astype(np.float32)/255
        g = arr[...,1].astype(np.float32)/255
        b = arr[...,2].astype(np.float32)/255
        maxc = np.maximum(np.maximum(r,g), b)
        minc = np.minimum(np.minimum(r,g), b)
        diff = maxc - minc + 1e-9
        hue = np.zeros_like(maxc)
        mask = maxc == r
        hue[mask] = ((g[mask]-b[mask])/diff[mask]) % 6
        mask = (maxc == g) & (~mask)
        hue[mask] = ((b[mask]-r[mask])/diff[mask]) + 2
        mask = (maxc == b) & (~mask)
        hue[mask] = ((r[mask]-g[mask])/diff[mask]) + 4
        hue = hue / 6.0
        return (hue * 255).astype(np.float32)
    return _compute_key_array(arr, "luminance")

def pixel_sort_with_structure(img, mode, invert, direction="horizontal", segment_size=0):
    arr = np.array(img.convert("RGB"))
    h, w, _ = arr.shape

    if direction == "horizontal":
        for y in range(h):
            row = arr[y]
            if segment_size <= 0:
                keys = _compute_key_array(row, mode)
                order = np.argsort(-keys) if invert else np.argsort(keys)
                arr[y] = row[order]
            else:
                for start in range(0, w, segment_size):
                    end = min(start + segment_size, w)
                    segment = row[start:end]
                    keys = _compute_key_array(segment, mode)
                    order = np.argsort(-keys) if invert else np.argsort(keys)
                    row[start:end] = segment[order]
                arr[y] = row
    else:
        for x in range(w):
            col = arr[:, x, :]
            if segment_size <= 0:
                keys = _compute_key_array(col, mode)
                order = np.argsort(-keys) if invert else np.argsort(keys)
                arr[:, x, :] = col[order]
            else:
                for start in range(0, h, segment_size):
                    end = min(start + segment_size, h)
                    segment = col[start:end]
                    keys = _compute_key_array(segment, mode)
                    order = np.argsort(-keys) if invert else np.argsort(keys)
                    col[start:end] = segment[order]
                arr[:, x, :] = col

    return Image.fromarray(arr, "RGB")

def generate_sort_frames(arr, mode, invert, direction, segment_size, steps=15):
    frames = []
    base_img = Image.fromarray(arr)
    sorted_img = pixel_sort_with_structure(base_img, mode, invert, direction, segment_size)
    sorted_arr = np.array(sorted_img)

    for step in range(steps + 1):
        t = step / steps
        frame_arr = (arr * (1 - t) + sorted_arr * t).astype(np.uint8)
        frames.append(Image.fromarray(frame_arr))

    return frames

class PixelSortCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="pixel_sort", description="Pixel-sort an image with options.")
    async def pixelsort(
        self,
        ctx: discord.ApplicationContext,
        user: Option(discord.Member, "Use a user's avatar", required=False) = None,
        emote: Option(str, "Server emote like <:name:id>", required=False) = None,
        image_url: Option(str, "Direct image URL", required=False) = None,
        mode: Option(str, "Sort key", choices=modes, required=False) = "luminance",
        invert: Option(bool, "Invert sort order", required=False) = False,
        direction: Option(str, "Sorting direction", choices=directions, required=False) = "horizontal",
        segment_size: Option(int, "Segment size (0 = full sort)", required=False, default=0),
        gif: Option(bool, "Generate a GIF of the process", required=False, default=False)
    ):
        await ctx.defer()
        image_data = None

        async with httpx.AsyncClient() as client:
            try:
                if user:
                    image_data = await user.avatar.read()
                elif emote:
                    match = re.match(r'<:(\w+):(\d+)>', emote)
                    if match:
                        em_id = int(match.group(2))
                        em = discord.utils.get(ctx.guild.emojis, id=em_id)
                        if em:
                            resp = await client.get(str(em.url))
                            resp.raise_for_status()
                            image_data = resp.content
                        else:
                            await ctx.respond("Emote not found.")
                            return
                    else:
                        await ctx.respond("Invalid emote format.")
                        return
                elif image_url:
                    resp = await client.get(image_url)
                    resp.raise_for_status()
                    image_data = resp.content
                else:
                    await ctx.respond("Please provide a user, emote, or image URL.")
                    return
            except Exception as e:
                await ctx.respond(f"Failed to fetch image: {e}")
                return

        try:
            base_img = _resize_keep_aspect(Image.open(BytesIO(image_data)).convert("RGB"))
            arr = np.array(base_img)

            if gif:
                frames = generate_sort_frames(arr, mode, invert, direction, segment_size)
                buf = BytesIO()
                frames[0].save(
                    buf,
                    format="GIF",
                    save_all=True,
                    append_images=frames[1:],
                    duration=100,
                    loop=0
                )
                buf.seek(0)
                file = discord.File(buf, filename="pixelsort.gif")
                embed = discord.Embed(title="Here's your pixel-sort GIF.", color=discord.Color(0x9FC6F6))
                embed.set_image(url="attachment://pixelsort.gif")
                await ctx.respond(file=file, embed=embed)
            else:
                out_img = pixel_sort_with_structure(base_img, mode, invert, direction, segment_size)
                buf = BytesIO()
                out_img.save(buf, format="PNG")
                buf.seek(0)
                file = discord.File(buf, filename="pixelsort.png")
                embed = discord.Embed(title="Here's your pixel-sort image.", color=discord.Color(0x9FC6F6))
                embed.set_image(url="attachment://pixelsort.png")
                await ctx.respond(file=file, embed=embed)

        except Exception as e:
            await ctx.respond(f"Error processing image: {e}")

async def setup(bot):
    await bot.add_cog(PixelSortCog(bot))