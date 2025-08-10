import discord
from discord.ext import commands
import os
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

class RandomSong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        client_id = os.environ.get("SPOTID")
        client_secret = os.environ.get("SPOTSEC")
        self.spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

    @commands.slash_command(name="random_song", description="Get a random song from Spotify")
    async def random_song(self, ctx: discord.ApplicationContext, artist: discord.Option(str, "Artist name", required=False, autocomplete=False) = None):
        await ctx.defer()
        query = f"artist:{artist}" if artist else "year:2022"
        try:
            results = self.spotify.search(q=query, type="track", limit=20)
        except Exception:
            await ctx.respond("Error fetching from Spotify. Try again later.")
            return
        tracks = results.get("tracks", {}).get("items", [])
        if not tracks:
            await ctx.respond("No songs found.")
            return
        track = random.choice(tracks)
        track_name = track["name"]
        artists = ", ".join([a["name"] for a in track["artists"]])
        url = track["external_urls"]["spotify"]
        await ctx.respond(f"🎵 **{track_name}** by **{artists}**\nListen here: {url}")

def setup(bot):
    bot.add_cog(RandomSong(bot))