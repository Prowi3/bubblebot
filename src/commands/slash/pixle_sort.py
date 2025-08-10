import discord
from discord.ext import commands
from discord.commands import Option
import numpy as np
from PIL import Image, ImageSequence
import io
import cv2

MAX_DIM = 1024

class PixelSort(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="pixelsort", description="Pixel-sort an image for glitch/art effects")
    async def pixelsort(
        self,
        ctx,
        mode: Option(str, "Sorting mode", choices=["luminance", "hue", "red", "green", "blue"], required=True),
        structure: Option(str, "Sort type", choices=["full", "structured"], required=True),
        reverse: Option(bool, "Reverse the pixel sorting", required=False, default=False),
        gif: Option(bool, "Export as GIF (loops sorted ↔ original)", required=False, default=False),
        attachment: Option(discord.Attachment, "Image to pixel sort", required=True)
    ):
        await ctx.defer()

        # Load image
        img_bytes = await attachment.read()
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

        # Resize to keep under MAX_DIM
        ratio = min(MAX_DIM / img.width, MAX_DIM / img.height, 1)
        if ratio < 1:
            img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)

        img_np = np.array(img)

        # Generate mask if "structured" mode is selected
        mask = None
        if structure == "structured":
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)  # Detect edges
            mask = edges > 0  # Boolean mask

        # Apply pixel sorting
        sorted_img_np = self.pixel_sort(img_np, mode, reverse, mask)

        # Handle output
        if gif:
            frames = [Image.fromarray(sorted_img_np), img]
            buf = io.BytesIO()
            frames[0].save(buf, format="GIF", save_all=True, append_images=[frames[1]], loop=0, duration=500)
            buf.seek(0)
            await ctx.respond(file=discord.File(buf, filename="pixelsort.gif"))
        else:
            buf = io.BytesIO()
            Image.fromarray(sorted_img_np).save(buf, format="PNG")
            buf.seek(0)
            await ctx.respond(file=discord.File(buf, filename="pixelsort.png"))

    def pixel_sort(self, img_np, mode, reverse=False, mask=None):
        """Apply pixel sorting by rows"""
        h, w, c = img_np.shape
        sorted_img = np.copy(img_np)

        if mode == "luminance":
            values = np.dot(sorted_img[..., :3], [0.299, 0.587, 0.114])
        elif mode == "hue":
            hsv = cv2.cvtColor(sorted_img, cv2.COLOR_RGB2HSV)
            values = hsv[..., 0]
        elif mode == "red":
            values = sorted_img[..., 0]
        elif mode == "green":
            values = sorted_img[..., 1]
        elif mode == "blue":
            values = sorted_img[..., 2]
        else:
            raise ValueError("Invalid mode")

        for y in range(h):
            if mask is not None:
                indices = np.where(mask[y])[0]
                if len(indices) > 1:
                    segment = sorted_img[y, indices]
                    sort_vals = values[y, indices]
                    sorted_segment = segment[np.argsort(sort_vals)]
                    if reverse:
                        sorted_segment = sorted_segment[::-1]
                    sorted_img[y, indices] = sorted_segment
            else:
                sort_idx = np.argsort(values[y])
                if reverse:
                    sort_idx = sort_idx[::-1]
                sorted_img[y] = sorted_img[y, sort_idx]

        return sorted_img

def setup(bot):
    bot.add_cog(PixelSort(bot))