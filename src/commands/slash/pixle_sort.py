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
        mask = (maxc == g) & (~mask)
        hue[mask] = ((b[mask]-r[mask])/diff[mask]) + 2
        mask = (maxc == b) & (~mask)
        hue[mask] = ((r[mask]-g[mask])/diff[mask]) + 4
        hue = hue / 6.0
        return (hue * 255).astype(np.float32)
    return _compute_key_array(arr, "luminance")

def pixel_sort_frame(img, mode, invert):
    arr = np.array(img.convert("RGB"))
    h, w, _ = arr.shape
    for y in range(h):
        row = arr[y]
        keys = _compute_key_array(row, mode)
        if invert:
            order = np.argsort(-keys)
        else:
            order = np.argsort(keys)
        arr[y] = row[order]
    return Image.fromarray(arr, "RGB")

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
            out_img = pixel_sort_frame(base_img, mode, invert)

            filename = "pixelsort.png"
            out_img.save(filename)

            file = discord.File(filename)
            embed_color = discord.Color(0x9FC6F6)
            embed = discord.Embed(title="Here's your image.", color=embed_color)
            embed.set_image(url=f"attachment://{filename}")

            await ctx.respond(file=file, embed=embed)
        except Exception as e:
            await ctx.respond(f"Error: {e}")

def setup(bot):
    bot.add_cog(PixelSortCog(bot))