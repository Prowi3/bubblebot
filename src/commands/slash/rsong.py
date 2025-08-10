import discord
import os
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random

class RandomSong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        client_id = os.environ.get('SPOTID')
        client_secret = os.environ.get('SPOTSEC')
        self.spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

        # Categories with Spotify playlist URIs or search queries
        self.categories = {
            "top_songs": "top hits",  # Search query example
            "top_of_the_week": "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",  # Top 50 Global
            "pop": "spotify:playlist:37i9dQZF1DXcZDD7cfEKhW",          # Today's Top Hits (Pop)
            "rock": "spotify:playlist:37i9dQZF1DWXRqgorJj26U",         # Rock Classics
            "hiphop": "spotify:playlist:37i9dQZF1DX0XUsuxWHRQd",       # RapCaviar (Hip-hop)
            "jazz": "spotify:playlist:37i9dQZF1DXbITWG1ZJKYt",         # Jazz Classics
            "classical": "spotify:playlist:37i9dQZF1DWWEJlAGA9gs0",     # Classical Essentials
            "electronic": "spotify:playlist:37i9dQZF1DX0BcQWzuB7ZO",   # ElectroNOW
            "country": "spotify:playlist:37i9dQZF1DX1lVhptIYRda",      # Hot Country
            "latin": "spotify:playlist:37i9dQZF1DX10zKzsJ2jva",        # Viva Latino
            "indie": "spotify:playlist:37i9dQZF1DX2Nc3B70tvx0",        # Indie Pop
            "blues": "spotify:playlist:37i9dQZF1DXd9rSDyQguIk",        # Blues Classics
        }

        self.recent_songs = []
        self.max_recent = 20

    def _add_recent(self, song_uri):
        self.recent_songs.append(song_uri)
        if len(self.recent_songs) > self.max_recent:
            self.recent_songs.pop(0)

    async def _get_random_track_from_playlist(self, playlist_uri):
        playlist = self.spotify.playlist(playlist_uri)
        total_tracks = playlist['tracks']['total']
        if total_tracks == 0:
            return None
        tries = 0
        while tries < 10:
            offset = random.randint(0, total_tracks - 1)
            tracks = self.spotify.playlist_tracks(playlist_uri, limit=1, offset=offset)
            track = tracks['items'][0]['track']
            if track['uri'] not in self.recent_songs:
                return track
            tries += 1
        return None

    async def _get_random_track_from_search(self, query):
        tries = 0
        while tries < 10:
            offset = random.randint(0, 999)
            results = self.spotify.search(q=query, type='track', limit=1, offset=offset)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                if track['uri'] not in self.recent_songs:
                    return track
            tries += 1
        return None

    @commands.slash_command(
        name="random_song", 
        description="Get a random song from Spotify!"
    )
    async def random_song(
        self, 
        ctx,
        category: discord.Option(
            str, 
            "Choose category or genre", 
            required=False, 
            choices=["random", *list([
                "top_songs", "top_of_the_week", "pop", "rock", "hiphop", 
                "jazz", "classical", "electronic", "country", "latin", 
                "indie", "blues"
            ])]
        ) = "random"
    ):
        await ctx.defer()

        if category == "random":
            category = random.choice(list(self.categories.keys()))

        if category in self.categories:
            source = self.categories[category]

            if source.startswith("spotify:playlist:"):
                track = await self._get_random_track_from_playlist(source)
            else:
                track = await self._get_random_track_from_search(source)
        else:
            track = await self._get_random_track_from_search("year:2022")

        if track is None:
            await ctx.respond("Couldn't find a new song right now, try again later!")
            return

        self._add_recent(track['uri'])
        track_url = track['external_urls']['spotify']
        track_name = track['name']
        artists = ", ".join(artist['name'] for artist in track['artists'])
        await ctx.respond(
            f"Here's a random **{category.replace('_', ' ')}** song:\n"
            f"**{track_name}** by {artists}\n{track_url}"
        )

def setup(bot):
    bot.add_cog(RandomSong(bot))