import discord
from discord.ext import commands
from discord.commands import Option
import aiohttp
import re
from io import BytesIO
from PIL import Image
import numpy as np

MAX_DIM = 1024

modes = [
    "luminance", "hue", "red", "green", "blue",
    "inverted_luminance", "random_noise", "edge_brightness"
]

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
        mask2 = (maxc == g) & (~mask)
        hue[mask2] = ((b[mask2]-r[mask2])/diff[mask2]) + 2
        mask3 = (maxc == b) & (~mask) & (~mask2)
        hue[mask3] = ((r[mask3]-g[mask3])/diff[mask3]) + 4
        hue = hue / 6.0
        return (hue * 255).astype(np.float32)
    return _compute_key_array(arr, "luminance")

def pixel_sort_frame_smooth(img: Image.Image, mode: str, invert: bool, progress: float, direction: str = "horizontal"):
    arr = np.array(img.convert("RGB"))
    h, w, _ = arr.shape
    out = np.zeros_like(arr, dtype=np.float32)

    if direction == "horizontal":
        for y in range(h):
            row = arr[y].astype(np.float32)
            keys = _compute_key_array(row, mode)
            order = np.argsort(-keys if invert else keys, kind='stable')
            target_pos = np.empty(w, dtype=np.float32)
            target_pos[order] = np.arange(w, dtype=np.float32)
            orig_pos = np.arange(w, dtype=np.float32)
            pos = (1.0 - progress) * orig_pos + progress * target_pos
            sort_idx = np.argsort(pos)
            pos_sorted = pos[sort_idx] + np.arange(w, dtype=np.float32) * 1e-7
            for c in range(3):
                vals_sorted = row[sort_idx, c]
                out[y, :, c] = np.interp(np.arange(w, dtype=np.float32), pos_sorted, vals_sorted)

    elif direction == "vertical":
        for x in range(w):
            col = arr[:, x].astype(np.float32)
            keys = _compute_key_array(col, mode)
            order = np.argsort(-keys if invert else keys, kind='stable')
            target_pos = np.empty(h, dtype=np.float32)
            target_pos[order] = np.arange(h, dtype=np.float32)
            orig_pos = np.arange(h, dtype=np.float32)
            pos = (1.0 - progress) * orig_pos + progress * target_pos
            sort_idx = np.argsort(pos)
            pos_sorted = pos[sort_idx] + np.arange(h, dtype=np.float32) * 1e-7
            for c in range(3):
                vals_sorted = col[sort_idx, c]
                out[:, x, c] = np.interp(np.arange(h, dtype=np.float32), pos_sorted, vals_sorted)

    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

async def make_pixelsort_gif_and_send(ctx, base_img: Image.Image, mode: str, invert: bool,
                                       duration_seconds: float = 5.0, frames: int = 40,
                                       max_dim: int = 512, colors: int = 128,
                                       direction: str = "horizontal"):
    if max(base_img.size) > max_dim:
        base_img = _resize_keep_aspect(base_img, max_dim)
    frame_images = []
    for i in range(frames):
        progress = i / (frames - 1)
        frame = pixel_sort_frame_smooth(base_img, mode, invert, progress, direction)
        frame_images.append(frame)
    paletted = [f.convert('P', palette=Image.ADAPTIVE, colors=colors) for f in frame_images]
    buf = BytesIO()
    duration_ms = int((duration_seconds / frames) * 1000)
    paletted[0].save(
        buf,
        format='GIF',
        save_all=True,
        append_images=paletted[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
        disposal=2
    )
    buf.seek(0)
    file = discord.File(buf, filename="pixelsort.gif")
    embed_color = discord.Color(0x9FC6F6)
    embed = discord.Embed(title="Here's your pixel-sort GIF.", color=embed_color)
    embed.set_image(url="attachment://pixelsort.gif")
    await ctx.respond(file=file, embed=embed)

class PixelSortCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="pixel_sort", description="Pixel-sort an image.")
    async def pixelsort(
        self,
        ctx: discord.ApplicationContext,
        user: Option(discord.Member, "Use a user's avatar", required=False) = None,
        emote: Option(str, "Server emote like <:name:id>", required=False) = None,
        image_url: Option(str, "Direct image URL", required=False) = None,
        mode: Option(str, "Sort key", choices=modes, required=False) = "luminance",
        invert: Option(bool, "Invert sort order", required=False) = False,
        gif: Option(bool, "Output as 5s GIF", required=False) = False,
        direction: Option(str, "Sort direction", choices=["horizontal", "vertical"], required=False) = "horizontal"
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
                await make_pixelsort_gif_and_send(ctx, base_img, mode, invert, direction=direction)
            else:
                out_img = pixel_sort_frame_smooth(base_img, mode, invert, 1.0, direction=direction)
                buf = BytesIO()
                out_img.save(buf, format="PNG")
                buf.seek(0)
                file = discord.File(buf, filename="pixelsort.png")
                embed_color = discord.Color(0x9FC6F6)
                embed = discord.Embed(title="Here's your image.", color=embed_color)
                embed.set_image(url="attachment://pixelsort.png")
                await ctx.respond(file=file, embed=embed)
        except Exception as e:
            await ctx.respond(f"Error: {e}")

def setup(bot):
    bot.add_cog(PixelSortCog(bot))