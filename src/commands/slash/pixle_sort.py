import discord
from discord.ext import commands
from discord.commands import Option
import aiohttp
import re
from io import BytesIO
from PIL import Image, ImageDraw
import numpy as np

MAX_DIM = 512  # smaller for GIF performance

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

def _sort_segment(segment, mode, invert):
    keys = _compute_key_array(segment, mode)
    order = np.argsort(-keys) if invert else np.argsort(keys)
    return segment[order]

def generate_sort_frames(arr, mode, invert, direction, segment_size, steps=10):
    arr = arr.copy()
    h, w, _ = arr.shape
    frames = []

    # Prepare all segments info to interpolate
    if direction == "horizontal":
        # For each row, get all segments and their sorted versions
        segments = []
        for y in range(h):
            row = arr[y]
            row_segments = []
            if segment_size <= 0:
                sorted_row = _sort_segment(row, mode, invert)
                row_segments.append((0, w, row, sorted_row))
            else:
                for start in range(0, w, segment_size):
                    end = min(start + segment_size, w)
                    seg = row[start:end]
                    sorted_seg = _sort_segment(seg, mode, invert)
                    row_segments.append((start, end, seg, sorted_seg))
            segments.append(row_segments)

        for step in range(steps + 1):
            frame = np.zeros_like(arr)
            t = step / steps
            for y in range(h):
                row_img = []
                for (start, end, orig_seg, sorted_seg) in segments[y]:
                    length = end - start
                    interp_seg = np.zeros_like(orig_seg)
                    for i in range(length):
                        orig_pos = i
                        sorted_pos = np.where((sorted_seg == orig_seg[i]).all(axis=1))[0]
                        # fallback if np.where is empty (shouldn't happen)
                        sorted_pos = sorted_pos[0] if len(sorted_pos) > 0 else i
                        interp_pos = int(orig_pos * (1 - t) + sorted_pos * t)
                        interp_pos = max(0, min(length - 1, interp_pos))
                        interp_seg[interp_pos] = orig_seg[i]
                    row_img.append(interp_seg)
                frame[y] = np.concatenate(row_img, axis=0)
            frames.append(frame)

    else:  # vertical
        segments = []
        for x in range(w):
            col = arr[:, x, :]
            col_segments = []
            if segment_size <= 0:
                sorted_col = _sort_segment(col, mode, invert)
                col_segments.append((0, h, col, sorted_col))
            else:
                for start in range(0, h, segment_size):
                    end = min(start + segment_size, h)
                    seg = col[start:end]
                    sorted_seg = _sort_segment(seg, mode, invert)
                    col_segments.append((start, end, seg, sorted_seg))
            segments.append(col_segments)

        for step in range(steps + 1):
            frame = np.zeros_like(arr)
            t = step / steps
            for x in range(w):
                col_img = []
                for (start, end, orig_seg, sorted_seg) in segments[x]:
                    length = end - start
                    interp_seg = np.zeros_like(orig_seg)
                    for i in range(length):
                        orig_pos = i
                        sorted_pos = np.where((sorted_seg == orig_seg[i]).all(axis=1))[0]
                        sorted_pos = sorted_pos[0] if len(sorted_pos) > 0 else i
                        interp_pos = int(orig_pos * (1 - t) + sorted_pos * t)
                        interp_pos = max(0, min(length - 1, interp_pos))
                        interp_seg[interp_pos] = orig_seg[i]
                    col_img.append(interp_seg)
                col_pixels = np.concatenate(col_img, axis=0)
                frame[:, x, :] = col_pixels
            frames.append(frame)

    pil_frames = [Image.fromarray(frame, "RGB") for frame in frames]
    return pil_frames

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
        segment_size: Option(int, "Segment size to preserve structure (0 = full sort)", required=False, default=0),
        gif: Option(bool, "Generate a GIF showing the sorting process", required=False, default=False)
    ):
        await ctx.defer()
        image_data = None
        async with aiohttp.ClientSession() as session:
            if user:
                image_data = await user.avatar.read()
            elif emote:
                match = re.match(r'<:(\w+):(\d+)>', emote)
                if match:
                    em_id = int(match.group(2))
                    em = discord.utils.get(ctx.guild.emojis, id=em_id)
                    if em:
                        async with session.get(str(em.url)) as resp:
                            image_data = await resp.read()
                else:
                    await ctx.respond("Invalid emote format.")
                    return
            elif image_url:
                async with session.get(image_url) as resp:
                    image_data = await resp.read()
            else:
                await ctx.respond("Please provide a user, emote, or image URL.")
                return

        try:
            base_img = _resize_keep_aspect(Image.open(BytesIO(image_data)).convert("RGB"))
            arr = np.array(base_img)

            if gif:
                frames = generate_sort_frames(arr, mode, invert, direction, segment_size, steps=15)
                buf = BytesIO()
                frames[0].save(
                    buf,
                    format="GIF",
                    save_all=True,
                    append_images=frames[1:],
                    duration=100,
                    loop=0,
                    disposal=2,
                    optimize=False,
                )
                buf.seek(0)
                file = discord.File(buf, filename="pixelsort.gif")
                embed_color = discord.Color(0x9FC6F6)
                embed = discord.Embed(title="Here's your pixel-sort GIF.", color=embed_color)
                embed.set_image(url="attachment://pixelsort.gif")
                await ctx.respond(file=file, embed=embed)

            else:
                out_img = pixel_sort_with_structure(base_img, mode, invert, direction, segment_size)
                buf = BytesIO()
                out_img.save(buf, format="PNG")
                buf.seek(0)
                file = discord.File(buf, filename="pixelsort.png")
                embed_color = discord.Color(0x9FC6F6)
                embed = discord.Embed(title="Here's your pixel-sort image.", color=embed_color)
                embed.set_image(url="attachment://pixelsort.png")
                await ctx.respond(file=file, embed=embed)

        except Exception as e:
            await ctx.respond(f"Error: {e}")

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
    else:  # vertical
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

async def setup(bot):
    await bot.add_cog(PixelSortCog(bot))