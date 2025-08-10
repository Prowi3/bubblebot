import os
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import aiohttp
from io import BytesIO
from PIL import Image
import discord
from discord.ext import commands
from discord.commands import Option

class RandomSong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spotify = None
        self.recent = []

    def _ensure_spotify(self):
        if self.spotify:
            return
        client_id = os.environ.get("SPOTID")
        client_secret = os.environ.get("SPOTSEC")
        if not client_id or not client_secret:
            raise RuntimeError("missing spotify credentials")
        self.spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

    async def _get_dominant_color(self, url):
        if not url:
            return discord.Color.blurple()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return discord.Color.blurple()
                    data = await resp.read()
            img = Image.open(BytesIO(data)).convert("RGBA").resize((50, 50))
            pixels = [p for p in img.getdata() if p[3] > 0]
            if not pixels:
                return discord.Color.blurple()
            r = sum(p[0] for p in pixels) // len(pixels)
            g = sum(p[1] for p in pixels) // len(pixels)
            b = sum(p[2] for p in pixels) // len(pixels)
            return discord.Color.from_rgb(r, g, b)
        except Exception:
            return discord.Color.blurple()

    @commands.slash_command(name="random_song", description="Get a random song from Spotify")
    async def random_song(self, ctx: discord.ApplicationContext, artist: Option(str, "Artist name", required=False, autocomplete=True) = None):
        await ctx.defer()
        try:
            self._ensure_spotify()
        except Exception:
            await ctx.respond("Spotify not configured.", ephemeral=True)
            return
        query = f"artist:{artist}" if artist else "year:2022"
        try:
            results = self.spotify.search(q=query, type="track", limit=20)
        except Exception:
            await ctx.respond("Spotify search failed.", ephemeral=True)
            return
        tracks = [t for t in results.get("tracks", {}).get("items", []) if t.get("uri") not in self.recent]
        if not tracks:
            self.recent.clear()
            tracks = results.get("tracks", {}).get("items", [])
            if not tracks:
                await ctx.respond("No songs found.", ephemeral=True)
                return
        track = random.choice(tracks)
        self.recent.append(track.get("uri"))
        if len(self.recent) > 30:
            self.recent.pop(0)
        name = track.get("name")
        artists = ", ".join(a.get("name") for a in track.get("artists", []))
        album = track.get("album", {}).get("name", "Unknown")
        url = track.get("external_urls", {}).get("spotify")
        images = track.get("album", {}).get("images") or []
        image_url = images[0]["url"] if images else None
        color = await self._get_dominant_color(image_url)
        embed = discord.Embed(title=name or "Unknown", url=url, description=f"By {artists}", color=color)
        embed.add_field(name="Album", value=album, inline=True)
        if image_url:
            embed.set_thumbnail(url=image_url)
        await ctx.respond(embed=embed)

    @random_song.autocomplete("artist")
    async def artist_autocomplete(self, interaction: discord.Interaction, current: str):
        if not current:
            return []
        try:
            self._ensure_spotify()
        except Exception:
            return []
        try:
            results = self.spotify.search(q=current, type="artist", limit=5)
            artists = results.get("artists", {}).get("items", [])
            return [discord.OptionChoice(name=a.get("name"), value=a.get("name")) for a in artists if a.get("name")]
        except Exception:
            return []

def setup(bot):
    bot.add_cog(RandomSong(bot))