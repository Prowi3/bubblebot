import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random

class RandomSong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="random_song", description="Get a random Song from Spotify!")
    async def random_song(self, ctx):
        spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
        offset = random.randint(0, 1000)
        
        results = spotify.search(q='genre:"pop"', type='track', limit=1, offset=offset)
        
        track = results['tracks']['items'][0]
        
        name = track['name']
        artists = ', '.join([artist['name'] for artist in track['artists']])
        album = track['album']['name']
        preview_url = track['preview_url']
        
        embed = discord.Embed(title=name, description=f'By: {artists}\nAlbum: {album}', color=discord.Color.green())
        if preview_url:
            embed.add_field(name="Preview", value=f"[Click here to preview]({preview_url})")
        else:
            embed.add_field(name="Preview", value="Preview not available")

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(RandomSong(bot))