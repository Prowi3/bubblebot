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

        self.categories = {
            "top_songs": "top hits",  # search query
            "top_of_the_week": "37i9dQZF1DXcBWIGoYBM5M",  # Top 50 Global
            "pop": "37i9dQZF1DXcZDD7cfEKhW",          # Today's Top Hits (Pop)
            "rock": "37i9dQZF1DWXRqgorJj26U",         # Rock Classics
            "hiphop": "37i9dQZF1DX0XUsuxWHRQd",       # RapCaviar (Hip-hop)
            "jazz": "37i9dQZF1DXbITWG1ZJKYt",         # Jazz Classics
            "classical": "37i9dQZF1DWWEJlAGA9gs0",     # Classical Essentials
            "electronic": "37i9dQZF1DX0BcQWzuB7ZO",   # ElectroNOW
            "country": "37i9dQZF1DX1lVhptIYRda",      # Hot Country
            "latin": "37i9dQZF1DX10zKzsJ2jva",        # Viva Latino
            "indie": "37i9dQZF1DX2Nc3B70tvx0",        # Indie Pop
            "blues": "37i9dQZF1DXd9rSDyQguIk",        # Blues Classics
        }

        self.recent_songs = []
        self.max_recent = 20

    def _add_recent(self, song_uri):
        self.recent_songs.append(song_uri)
        if len(self.recent_songs) > self.max_recent:
            self.recent_songs.pop(0)

    async def _get_random_track_from_playlist(self, playlist_id):
        playlist = self.spotify.playlist(playlist_id)
        total_tracks = playlist['tracks']['total']
        if total_tracks == 0:
            return None
        tries = 0
        while tries < 10:
            offset = random.randint(0, total_tracks - 1)
            tracks = self.spotify.playlist_tracks(playlist_id, limit=1, offset=offset)
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

            # If the category is 'top_songs', treat source as search query
            if category == "top_songs":
                track = await self._get_random_track_from_search(source)
            else:
                # Otherwise, treat source as playlist ID
                track = await self._get_random_track_from_playlist(source)
        else:
            # fallback search
            track = await self._get_random_track_from_search("year:2022")

        if track is None:
            await ctx.respond("Couldn't find a new song right now, try again later!")
            return

        self._add_recent(track['uri'])

        embed = discord.Embed(
            title=track['name'],
            url=track['external_urls']['spotify'],
            description=f"By {', '.join(artist['name'] for artist in track['artists'])}",
            color=discord.Color.green()
        )

        if track['album']['images']:
            embed.set_thumbnail(url=track['album']['images'][0]['url'])

        embed.set_footer(text=f"Category: {category.replace('_', ' ').title()}")

        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(RandomSong(bot))