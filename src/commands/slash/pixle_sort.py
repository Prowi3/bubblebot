import discord
from discord.ext import commands
from discord.commands import Option
import aiohttp
import re
from io import BytesIO
from PIL import Image
import numpy as np

MAX_DIM = 1024

modes = ["luminance", "hue", "red", "green", "blue"]
directions = ["rows", "columns"]

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

def _find_runs(mask):
    if mask.size == 0:
        return []
    diffs = np.diff(mask.astype(np.int8))
    starts = np.where(diffs == 1)[0] + 1
    ends = np.where(diffs == -1)[0]
    if mask[0]:
        starts = np.concatenate(([0], starts))
    if mask[-1]:
        ends = np.concatenate((ends, [mask.size-1]))
    return [(int(s), int(e)) for s,e in zip(starts, ends)]

def pixel_sort_frame(img, mode, direction, threshold, min_run, invert, progress=1.0):
    arr = np.array(img.convert("RGB"))
    h, w, _ = arr.shape
    if direction == "columns":
        arr = np.transpose(arr, (1,0,2))
        H, W = arr.shape[:2]
    else:
        H, W = h, w

    for y in range(H):
        row = arr[y]
        keys = _compute_key_array(row, mode)
        mask = keys <= threshold if invert else keys > threshold
        runs = _find_runs(mask)
        for start, end in runs:
            if (end - start + 1) < min_run:
                continue
            segment = row[start:end+1]
            seg_keys = keys[start:end+1]
            order = np.argsort(seg_keys)
            cut = int(len(order) * progress)
            order_partial = np.concatenate([order[:cut], order[cut:]])
            sorted_segment = segment[order_partial]
            row[start:end+1] = sorted_segment
        arr[y] = row

    if direction == "columns":
        arr = np.transpose(arr, (1,0,2))
    return Image.fromarray(arr, "RGB")

class PixelSortCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="pixelsort", description="Pixel-sort an image (static or GIF).")
    async def pixelsort(
        self,
        ctx: discord.ApplicationContext,
        user: Option(discord.Member, "Use a user's avatar", required=False) = None,
        emote: Option(str, "Server emote like <:name:id>", required=False) = None,
        image_url: Option(str, "Direct image URL", required=False) = None,
        mode: Option(str, "Sort key", choices=modes, required=False) = "luminance",
        direction: Option(str, "Sort along rows or columns", choices=directions, required=False) = "rows",
        threshold: Option(float, "Threshold (0-255)", required=False) = 128.0,
        min_run: Option(int, "Min contiguous run to sort", required=False) = 4,
        invert: Option(bool, "Invert threshold selection", required=False) = False,
        gif: Option(bool, "Output an animated GIF", required=False) = False,
        frames: Option(int, "Number of frames if gif=true", required=False) = 8,
        fps: Option(int, "Frames per second if gif=true", required=False) = 10
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
            if gif:
                frame_list = []
                frames = max(2, min(60, frames or 8))
                for i in range(frames):
                    progress = (i+1) / frames
                    frame_img = pixel_sort_frame(
                        base_img.copy(), mode, direction,
                        max(0, min(255, threshold)), max(1, min_run),
                        invert, progress
                    )
                    frame_list.append(frame_img.convert("P", palette=Image.ADAPTIVE))
                buf = BytesIO()
                frame_list[0].save(buf, format="GIF", save_all=True,
                                   append_images=frame_list[1:], duration=int(1000/(fps or 10)),
                                   loop=0)
                buf.seek(0)
                await ctx.respond(file=discord.File(buf, filename="pixelsort.gif"))
            else:
                out_img = pixel_sort_frame(
                    base_img.copy(), mode, direction,
                    max(0, min(255, threshold)), max(1, min_run),
                    invert, progress=1.0
                )
                buf = BytesIO()
                out_img.save(buf, format="PNG")
                buf.seek(0)
                await ctx.respond(file=discord.File(buf, filename="pixelsort.png"))
        except Exception as e:
            await ctx.respond(f"Error: {e}")

def setup(bot):
    bot.add_cog(PixelSortCog(bot))