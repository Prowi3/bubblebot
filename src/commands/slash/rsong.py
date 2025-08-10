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
        self.recent = []

    @commands.slash_command(name="random_song", description="Get a random song from Spotify")
    async def random_song(self, ctx: discord.ApplicationContext, artist: discord.Option(str, "Artist name", required=False, autocomplete=True) = None):
        await ctx.defer()
        query = f"artist:{artist}" if artist else "year:2022"
        try:
            results = self.spotify.search(q=query, type="track", limit=30)
        except Exception:
            await ctx.respond("Error fetching from Spotify. Try again later.")
            return
        tracks = [t for t in results.get("tracks", {}).get("items", []) if t["uri"] not in self.recent]
        if not tracks:
            self.recent.clear()
            tracks = results.get("tracks", {}).get("items", [])
            if not tracks:
                await ctx.respond("No songs found.")
                return
        track = random.choice(tracks)
        self.recent.append(track["uri"])
        if len(self.recent) > 30:
            self.recent.pop(0)
        track_name = track["name"]
        artists = ", ".join([a["name"] for a in track["artists"]])
        album = track["album"]["name"]
        url = track["external_urls"]["spotify"]
        embed = discord.Embed(title=track_name, url=url, description=f"By {artists}", color=discord.Color.blurple())
        embed.add_field(name="Album", value=album, inline=True)
        if track["album"]["images"]:
            embed.set_thumbnail(url=track["album"]["images"][0]["url"])
        await ctx.respond(embed=embed)

    @random_song.autocomplete("artist")
    async def artist_autocomplete(self, interaction: discord.Interaction, current: str):
        if not current:
            return []
        try:
            results = self.spotify.search(q=current, type="artist", limit=10)
            artists = results.get("artists", {}).get("items", [])
            return [discord.OptionChoice(name=a["name"], value=a["name"]) for a in artists]
        except Exception:
            return []

def setup(bot):
    bot.add_cog(RandomSong(bot))