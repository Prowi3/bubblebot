import os
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import discord
from discord.ext import commands
from discord.commands import Option

class RandomSong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_spotify_client(self):
        client_id = os.environ.get("SPOTID")
        client_secret = os.environ.get("SPOTSEC")
        if not client_id or not client_secret:
            return None
        return spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

    @commands.slash_command(name="random_song", description="Get a random song from Spotify")
    async def random_song(self, ctx: discord.ApplicationContext, artist: Option(str, "Artist name", required=False) = None):
        await ctx.defer()
        spotify = self.get_spotify_client()
        if not spotify:
            await ctx.respond("Spotify credentials missing.", ephemeral=True)
            return
        query = f"artist:{artist}" if artist else "year:2022"
        try:
            results = spotify.search(q=query, type="track", limit=10)
            tracks = results.get("tracks", {}).get("items", [])
        except Exception:
            await ctx.respond("Spotify search failed.", ephemeral=True)
            return
        if not tracks:
            await ctx.respond("No songs found.", ephemeral=True)
            return
        track = random.choice(tracks)
        name = track["name"]
        artists = ", ".join(a["name"] for a in track["artists"])
        url = track["external_urls"]["spotify"]
        embed = discord.Embed(title=name, url=url, description=f"By {artists}", color=discord.Color.blurple())
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(RandomSong(bot))