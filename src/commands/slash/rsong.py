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
        if not client_id or not client_secret:
            raise RuntimeError("SPOTID and SPOTSEC env vars are required")
        self.spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

    @commands.slash_command(name="random_song", description="Get a random song from Spotify")
    async def random_song(self, ctx: discord.ApplicationContext, artist: discord.Option(str, "Search artist", required=False, autocomplete=True) = None):
        await ctx.defer()
        query = f"artist:{artist}" if artist else "year:2022"
        results = self.spotify.search(q=query, type="track", limit=10)
        tracks = results.get("tracks", {}).get("items", [])
        if not tracks:
            await ctx.respond("No songs found.")
            return
        track = random.choice(tracks)
        track_name = track["name"]
        artists = ", ".join([a["name"] for a in track["artists"]])
        url = track["external_urls"]["spotify"]
        album = track["album"]["name"]
        embed = discord.Embed(title=track_name, url=url, description=f"By {artists}", color=discord.Color.blurple())
        embed.add_field(name="Album", value=album)
        if track["album"]["images"]:
            embed.set_thumbnail(url=track["album"]["images"][0]["url"])
        await ctx.respond(embed=embed)

    async def random_song_autocomplete(self, interaction: discord.Interaction, current: str):
        if not current:
            return []
        results = self.spotify.search(q=current, type="artist", limit=5)
        artists = results.get("artists", {}).get("items", [])
        return [discord.OptionChoice(name=a["name"], value=a["name"]) for a in artists]

    @random_song.autocomplete("artist")
    async def artist_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self.random_song_autocomplete(interaction, current)

def setup(bot):
    bot.add_cog(RandomSong(bot))