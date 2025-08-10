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
directions = ["horizontal", "vertical"]


def _resize_keep_aspect(img: Image.Image, max_dim=MAX_DIM):
    w, h = img.size
    if max(w, h) <= max_dim:
        return img
    if w >= h:
        return img.resize((max_dim, int(h * (max_dim / w))), Image.LANCZOS)
    return img.resize((int(w * (max_dim / h)), max_dim), Image.LANCZOS)


def _compute_key_array(arr, mode):
    # arr is (N,3) row or column
    if mode == "luminance":
        r, g, b = [arr[..., i].astype(np.float32) for i in range(3)]
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    if mode == "inverted_luminance":
        r, g, b = [arr[..., i].astype(np.float32) for i in range(3)]
        return 255 - (0.2126 * r + 0.7152 * g + 0.0722 * b)
    if mode == "random_noise":
        return np.random.uniform(0, 255, size=arr.shape[0])
    if mode == "edge_brightness":
        lum = 0.2126 * arr[..., 0] + 0.7152 * arr[..., 1] + 0.0722 * arr[..., 2]
        left = np.roll(lum, 1)
        right = np.roll(lum, -1)
        diff = np.abs(left - right)
        return diff.astype(np.float32)
    if mode in ("red", "green", "blue"):
        return arr[..., {"red": 0, "green": 1, "blue": 2}[mode]].astype(np.float32)
    if mode == "hue":
        # compute hue per pixel in [0,255]
        r = arr[..., 0].astype(np.float32) / 255.0
        g = arr[..., 1].astype(np.float32) / 255.0
        b = arr[..., 2].astype(np.float32) / 255.0
        maxc = np.maximum(np.maximum(r, g), b)
        minc = np.minimum(np.minimum(r, g), b)
        diff = maxc - minc + 1e-9
        hue = np.zeros_like(maxc)
        mask = maxc == r
        hue[mask] = ((g[mask] - b[mask]) / diff[mask]) % 6
        mask2 = (maxc == g) & (~mask)
        hue[mask2] = ((b[mask2] - r[mask2]) / diff[mask2]) + 2
        mask3 = (maxc == b) & (~mask) & (~mask2)
        hue[mask3] = ((r[mask3] - g[mask3]) / diff[mask3]) + 4
        hue = hue / 6.0
        return (hue * 255).astype(np.float32)
    # fallback
    return _compute_key_array(arr, "luminance")


def pixel_sort_frame_smooth(img: Image.Image, mode: str, invert: bool, progress: float, structure: str, direction: str):
    """
    Sorts per-row (horizontal) or per-column (vertical) using same codepath.
    progress: 0.0..1.0
    """
    arr = np.array(img.convert("RGB"))
    # If vertical, rotate so columns become rows, then rotate back at end.
    rotated = False
    if direction == "vertical":
        arr = np.rot90(arr, 1)
        rotated = True

    h, w, _ = arr.shape
    out = np.zeros_like(arr, dtype=np.float32)

    for y in range(h):
        row = arr[y].astype(np.float32)
        keys = _compute_key_array(row, mode)

        if structure == "structured":
            edge_mask_row = _compute_key_array(row, "edge_brightness")
            # 70th percentile threshold — tweakable
            threshold = np.percentile(edge_mask_row, 70)
            mask = edge_mask_row >= threshold
            indices = np.where(mask)[0]

            if len(indices) > 1:
                keys_to_sort = keys[indices]
                order = np.argsort(-keys_to_sort if invert else keys_to_sort, kind="stable")

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
            order = np.argsort(-keys if invert else keys, kind="stable")
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

    if rotated:
        out = np.rot90(out, 3)

    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


async def make_pixelsort_gif_and_send(interaction: discord.Interaction, base_img: Image.Image, mode: str, invert: bool,
                                      structure: str, direction: str,
                                      duration_seconds: float = 2.0, frames: int = 30,
                                      max_dim: int = 320, colors: int = 64):
    """
    Creates a GIF (forward frames + reversed frames to loop back) and edits the original response.
    Defaults tuned to reduce file size (max_dim=320, colors=64) — adjust as needed.
    """
    if max(base_img.size) > max_dim:
        base_img = _resize_keep_aspect(base_img, max_dim)

    frame_images = []
    for i in range(frames):
        progress = i / (frames - 1)
        frame = pixel_sort_frame_smooth(base_img, mode, invert, progress, structure, direction)
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
    embed = discord.Embed(title="Here's your pixel-sort GIF.", color=discord.Color(0x9FC6F6))
    embed.set_image(url="attachment://pixelsort.gif")
    await interaction.edit_original_response(content=None, embed=embed, file=file, view=None)


async def make_pixelsort_image_and_send(interaction: discord.Interaction, base_img: Image.Image, mode: str, invert: bool,
                                        structure: str, direction: str,
                                        max_dim: int = 512):
    if max(base_img.size) > max_dim:
        base_img = _resize_keep_aspect(base_img, max_dim)
    out_img = pixel_sort_frame_smooth(base_img, mode, invert, 1.0, structure, direction)
    buf = BytesIO()
    out_img.save(buf, format="PNG")
    buf.seek(0)
    file = discord.File(buf, filename="pixelsort.png")
    embed = discord.Embed(title="Here's your pixel-sort image.", color=discord.Color(0x9FC6F6))
    embed.set_image(url="attachment://pixelsort.png")
    await interaction.edit_original_response(content=None, embed=embed, file=file, view=None)


class PixelSortOptionsView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext, base_img: Image.Image):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.base_img = base_img
        self.mode = "luminance"
        self.structure = "full"
        self.invert = False
        self.direction = "horizontal"

        # put each Select on its own row (Selects are full-width)
        self.add_item(ModeSelect(self, row=0))
        self.add_item(StructureSelect(self, row=1))
        self.add_item(InvertSelect(self, row=2))
        self.add_item(DirectionSelect(self, row=3))
        # two buttons sharing the final row
        self.add_item(GenerateImageButton(self, row=4))
        self.add_item(GenerateGifButton(self, row=4))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # only allow the original command user to interact
        return interaction.user == self.ctx.user


class ModeSelect(discord.ui.Select):
    def __init__(self, parent_view: PixelSortOptionsView, row: int = 0):
        options = [discord.SelectOption(label=m, value=m) for m in modes]
        super().__init__(placeholder="Select sort mode...", options=options, min_values=1, max_values=1, row=row)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.mode = self.values[0]
        await interaction.response.defer()


class StructureSelect(discord.ui.Select):
    def __init__(self, parent_view: PixelSortOptionsView, row: int = 1):
        options = [
            discord.SelectOption(label="Full", value="full"),
            discord.SelectOption(label="Structured", value="structured"),
        ]
        super().__init__(placeholder="Select sorting style...", options=options, min_values=1, max_values=1, row=row)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.structure = self.values[0]
        await interaction.response.defer()


class InvertSelect(discord.ui.Select):
    def __init__(self, parent_view: PixelSortOptionsView, row: int = 2):
        options = [
            discord.SelectOption(label="No", value="False"),
            discord.SelectOption(label="Yes", value="True"),
        ]
        super().__init__(placeholder="Invert sort order?", options=options, min_values=1, max_values=1, row=row)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.invert = (self.values[0] == "True")
        await interaction.response.defer()


class DirectionSelect(discord.ui.Select):
    def __init__(self, parent_view: PixelSortOptionsView, row: int = 3):
        options = [
            discord.SelectOption(label="Horizontal", value="horizontal"),
            discord.SelectOption(label="Vertical", value="vertical"),
        ]
        super().__init__(placeholder="Select sort direction...", options=options, min_values=1, max_values=1, row=row)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.direction = self.values[0]
        await interaction.response.defer()


class GenerateImageButton(discord.ui.Button):
    def __init__(self, parent_view: PixelSortOptionsView, row: int = 4):
        super().__init__(label="Generate Image", style=discord.ButtonStyle.primary, row=row)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        # Edit the original message to show generating state (this is the initial response)
        await interaction.response.edit_message(content="Generating...", embed=None, view=None)
        try:
            await make_pixelsort_image_and_send(
                interaction,
                self.parent_view.base_img,
                self.parent_view.mode,
                self.parent_view.invert,
                self.parent_view.structure,
                self.parent_view.direction
            )
        except Exception as e:
            # if something fails, send a followup so the user knows
            await interaction.followup.send(f"Error generating image: {e}", ephemeral=False)
        self.parent_view.stop()


class GenerateGifButton(discord.ui.Button):
    def __init__(self, parent_view: PixelSortOptionsView, row: int = 4):
        super().__init__(label="Generate GIF", style=discord.ButtonStyle.success, row=row)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="Generating...", embed=None, view=None)
        try:
            await make_pixelsort_gif_and_send(
                interaction,
                self.parent_view.base_img,
                self.parent_view.mode,
                self.parent_view.invert,
                self.parent_view.structure,
                self.parent_view.direction
            )
        except Exception as e:
            await interaction.followup.send(f"Error generating GIF: {e}", ephemeral=False)
        self.parent_view.stop()


class PixelSortCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._synced = False

    @commands.Cog.listener()
    async def on_ready(self):
        # try to sync slash commands if possible; fail gracefully if not
        if self._synced:
            return
        try:
            await self.bot.wait_until_ready()
            # bot.tree may not exist in some old builds — wrap in try/except
            try:
                await self.bot.tree.sync()
            except Exception:
                pass
        finally:
            self._synced = True

    @commands.slash_command(name="test", description="Pixel-sort an image with a GUI.")
    async def pixelsort(
        self,
        ctx: discord.ApplicationContext,
        user: Option(discord.Member, "Use a user's avatar", required=False) = None,
        emote: Option(str, "Server emote like <:name:id>", required=False) = None,
        image_url: Option(str, "Direct image URL", required=False) = None,
    ):
        # initial defer then respond with the view (not ephemeral)
        await ctx.defer()
        image_data = None
        async with aiohttp.ClientSession() as session:
            if user:
                image_data = await user.avatar.read()
            elif emote:
                match = re.match(r"<:(\w+):(\d+)>", emote)
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
        await ctx.respond("Select your pixel sort options, then click a button to generate.", view=view)


def setup(bot: commands.Bot):
    bot.add_cog(PixelSortCog(bot))