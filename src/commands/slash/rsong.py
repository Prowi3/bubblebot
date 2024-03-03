import discord
import os
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random

class RandomSong(commands.Cog):
    def __init__(self, bot):
        client_id = os.environ.get('SPOTID')
        client_secret = os.environ.get('SPOTSEC')
        self.bot = bot
        self.spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

    @commands.slash_command(name="random_song", description="Get a random song from Spotify!")
    async def random_song(self, ctx):
        offset = random.randint(0, 1000)
        results = self.spotify.search(q='year:2022', type='track', limit=1, offset=offset)

        if results['tracks']['items']:
            track_url = results['tracks']['items'][0]['external_urls']['spotify']
            await ctx.respond(f"Here's a random song from Spotify: {track_url}")
        else:
            await ctx.respond("No results found. Try again later.")

def setup(bot):
    bot.add_cog(RandomSong(bot))
