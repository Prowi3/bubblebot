import discord
from discord.ext import commands
import os
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import aiohttp
from io import BytesIO
from PIL import Image

class RandomSong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        client_id = os.environ.get("SPOTID")
        client_secret = os.environ.get("SPOTSEC")
        self.spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
        self.recent = []

    async def get_dominant_color(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return discord.Color.blurple()
                data = await resp.read()
        img = Image.open(BytesIO(data)).convert('RGBA').resize((50,50))
        pixels = list(img.getdata())
        pixels = [p for p in pixels if p[3] > 0]  # ignore transparent pixels
        r = sum(p[0] for p in pixels) // len(pixels)
        g = sum(p[1] for p in pixels) // len(pixels)
        b = sum(p[2] for p in pixels) // len(pixels)
        return discord.Color.from_rgb(r, g, b)

    @commands.slash_command(name="random_song", description="Get a random song from Spotify")
    async def random_song(self, ctx: discord.ApplicationContext, artist: discord.Option(str, "Artist name", required=False, autocomplete=True) = None):
        await ctx.defer()
        query = f"artist:{artist}" if artist else "year:2022"
        try:
            results = self.spotify.search(q=query, type="track", limit=20)
        except Exception:
            await ctx.respond("Spotify error.", ephemeral=True)
            return
        tracks = [t for t in results.get("tracks", {}).get("items", []) if t["uri"] not in self.recent]
        if not tracks:
            self.recent.clear()
            tracks = results.get("tracks", {}).get("items", [])
            if not tracks:
                await ctx.respond("No songs found.", ephemeral=True)
                return
        track = random.choice(tracks)
        self.recent.append(track["uri"])
        if len(self.recent) > 30:
            self.recent.pop(0)
        track_name = track["name"]
        artists = ", ".join([a["name"] for a in track["artists"]])
        album = track["album"]["name"]
        url = track["external_urls"]["spotify"]
        image_url = track["album"]["images"][0]["url"] if track["album"]["images"] else None
        color = await self.get_dominant_color(image_url) if image_url else discord.Color.blurple()
        embed = discord.Embed(title=track_name, url=url, description=f"By {artists}", color=color)
        embed.add_field(name="Album", value=album, inline=True)
        if image_url:
            embed.set_thumbnail(url=image_url)
        await ctx.respond(embed=embed)

    @random_song.autocomplete("artist")
    async def artist_autocomplete(self, interaction: discord.Interaction, current: str):
        if not current:
            return []
        try:
            results = self.spotify.search(q=current, type="artist", limit=5)
            artists = results.get("artists", {}).get("items", [])
            return [discord.OptionChoice(name=a["name"], value=a["name"]) for a in artists]
        except Exception:
            return []

def setup(bot):
    bot.add_cog(RandomSong(bot))