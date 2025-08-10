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

structures = ["full", "structured"]

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

def pixel_sort_frame_smooth(img: Image.Image, mode: str, invert: bool, progress: float, structure: str):
    arr = np.array(img.convert("RGB"))
    h, w, _ = arr.shape
    out = np.zeros_like(arr, dtype=np.float32)

    for y in range(h):
        row = arr[y].astype(np.float32)
        keys = _compute_key_array(row, mode)

        if structure == "structured":
            edge_mask_row = _compute_key_array(row, "edge_brightness")
            threshold = np.percentile(edge_mask_row, 70)
            mask = edge_mask_row >= threshold
            indices = np.where(mask)[0]

            if len(indices) > 1:
                keys_to_sort = keys[indices]
                if invert:
                    order = np.argsort(-keys_to_sort, kind='stable')
                else:
                    order = np.argsort(keys_to_sort, kind='stable')

                target_pos = np.empty(len(indices), dtype=np.float32)
                target_pos[order] = np.arange(len(indices), dtype=np.float32)
                orig_pos = np.arange(len(indices), dtype=np.float32)
                pos = (1.0 - progress) * orig_pos + progress * target_pos
                sort_idx = np.argsort(pos)
                pos_sorted = pos[sort_idx]
                pos_sorted = pos_sorted + np.arange(len(indices), dtype=np.float32) * 1e-7

                for c in range(3):
                    vals_sorted = row[indices[sort_idx], c]
                    out[y, indices, c] = np.interp(np.arange(len(indices), dtype=np.float32), pos_sorted, vals_sorted)

                out[y, ~mask, :] = row[~mask]
            else:
                out[y] = row
        else:
            if invert:
                order = np.argsort(-keys, kind='stable')
            else:
                order = np.argsort(keys, kind='stable')

            target_pos = np.empty(w, dtype=np.float32)
            target_pos[order] = np.arange(w, dtype=np.float32)
            orig_pos = np.arange(w, dtype=np.float32)
            pos = (1.0 - progress) * orig_pos + progress * target_pos
            sort_idx = np.argsort(pos)
            pos_sorted = pos[sort_idx]
            pos_sorted = pos_sorted + np.arange(w, dtype=np.float32) * 1e-7
            for c in range(3):
                vals_sorted = row[sort_idx, c]
                out[y, :, c] = np.interp(np.arange(w, dtype=np.float32), pos_sorted, vals_sorted)

    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

async def make_pixelsort_gif_and_send(ctx, base_img: Image.Image, mode: str, invert: bool,
                                       structure: str,
                                       duration_seconds: float = 2.0, frames: int = 30,
                                       max_dim: int = 512, colors: int = 128):
    if max(base_img.size) > max_dim:
        base_img = _resize_keep_aspect(base_img, max_dim)
    frame_images = []
    for i in range(frames):
        progress = i / (frames - 1)
        frame = pixel_sort_frame_smooth(base_img, mode, invert, progress, structure)
        frame_images.append(frame)

    reversed_frames = list(reversed(frame_images[:-1]))
    all_frames = frame_images + reversed_frames

    paletted = [f.convert('P', palette=Image.ADAPTIVE, colors=colors) for f in all_frames]
    buf = BytesIO()
    duration_ms = int((duration_seconds / len(all_frames)) * 1000)
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

class PixelSortOptionsView(discord.ui.View):
    def __init__(self, ctx, base_img):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.base_img = base_img
        self.mode = "luminance"
        self.structure = "full"
        self.invert = False
        self.gif = False

        self.add_item(ModeSelect(self))
        self.add_item(StructureSelect(self))
        self.add_item(InvertSelect(self))
        self.add_item(GifSelect(self))
        self.add_item(RunButton(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.ctx.author

class ModeSelect(discord.ui.Select):
    def __init__(self, parent_view):
        options = [
            discord.SelectOption(label=m, value=m) for m in modes
        ]
        super().__init__(placeholder="Select sort mode...", options=options, min_values=1, max_values=1)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.mode = self.values[0]
        await interaction.response.defer()

class StructureSelect(discord.ui.Select):
    def __init__(self, parent_view):
        options = [
            discord.SelectOption(label="Full", value="full"),
            discord.SelectOption(label="Structured", value="structured")
        ]
        super().__init__(placeholder="Select sorting style...", options=options, min_values=1, max_values=1)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.structure = self.values[0]
        await interaction.response.defer()

class InvertSelect(discord.ui.Select):
    def __init__(self, parent_view):
        options = [
            discord.SelectOption(label="No", value="False"),
            discord.SelectOption(label="Yes", value="True")
        ]
        super().__init__(placeholder="Invert sort order?", options=options, min_values=1, max_values=1)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.invert = (self.values[0] == "True")
        await interaction.response.defer()

class GifSelect(discord.ui.Select):
    def __init__(self, parent_view):
        options = [
            discord.SelectOption(label="No", value="False"),
            discord.SelectOption(label="Yes", value="True")
        ]
        super().__init__(placeholder="Output as GIF?", options=options, min_values=1, max_values=1)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.gif = (self.values[0] == "True")
        await interaction.response.defer()

class RunButton(discord.ui.Button):
    def __init__(self, parent_view):
        super().__init__(label="Run Pixel Sort", style=discord.ButtonStyle.primary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            if self.parent_view.gif:
                await make_pixelsort_gif_and_send(
                    self.parent_view.ctx,
                    self.parent_view.base_img,
                    self.parent_view.mode,
                    self.parent_view.invert,
                    self.parent_view.structure
                )
            else:
                out_img = pixel_sort_frame_smooth(
                    self.parent_view.base_img,
                    self.parent_view.mode,
                    self.parent_view.invert,
                    1.0,
                    self.parent_view.structure
                )
                buf = BytesIO()
                out_img.save(buf, format="PNG")
                buf.seek(0)
                file = discord.File(buf, filename="pixelsort.png")
                embed_color = discord.Color(0x9FC6F6)
                embed = discord.Embed(title="Here's your image.", color=embed_color)
                embed.set_image(url="attachment://pixelsort.png")
                await interaction.followup.send(file=file, embed=embed)
        except Exception as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
        self.parent_view.stop()

class PixelSortCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._synced = False

    @commands.Cog.listener()
    async def on_ready(self):
        if self._synced:
            return
        await self.bot.wait_until_ready()
        await self.bot.tree.sync()
        self._synced = True

    @commands.slash_command(name="modal", description="Pixel-sort an image with a GUI.")
    async def pixelsort(
        self,
        ctx: discord.ApplicationContext,
        user: Option(discord.Member, "Use a user's avatar", required=False) = None,
        emote: Option(str, "Server emote like <:name:id>", required=False) = None,
        image_url: Option(str, "Direct image URL", required=False) = None
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
        except Exception as e:
            await ctx.respond(f"Failed to load image: {e}")
            return

        view = PixelSortOptionsView(ctx, base_img)
        await ctx.respond("Select your pixel sort options and click **Run Pixel Sort**.", view=view)

def setup(bot):
    bot.add_cog(PixelSortCog(bot))