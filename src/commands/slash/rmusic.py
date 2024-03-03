import discord
import os
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random

class RandomSong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        client_id = os.environ['SPOT']
        self.spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=client_id))

    @commands.slash_command(name="random_song", description="Get a random Song from Spotify!")
    async def random_song(self, ctx):
        playlist_ids = [
            "37i9dQZF1DX4JAvHpjipBk",
            "37i9dQZF1DWTJ7xPn4vNaz",
        ]
        playlist_id = random.choice(playlist_ids)

        playlist = self.spotify.playlist_tracks(playlist_id, limit=50)
        tracks = playlist['items']
        
        random_track = random.choice(tracks)['track']
        
        name = random_track['name']
        artists = ', '.join([artist['name'] for artist in random_track['artists']])
        album = random_track['album']['name']
        preview_url = random_track['preview_url']
        
        embed = discord.Embed(title=name, description=f'By: {artists}\nAlbum: {album}', color=discord.Color.green())
        if preview_url:
            embed.add_field(name="Preview", value=f"[Click here to preview]({preview_url})")
        else:
            embed.add_field(name="Preview", value="Preview not available")

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(RandomSong(bot))
