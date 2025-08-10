import discord
import os
import json
import random
from pathlib import Path
from discord.ext import commands
from discord.ui import View, Button
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

RECENT_FILE = Path("data/recent_songs.json")
BAD_FILE = Path("data/bad_playlists.json")

def ms_to_minsec(ms: int) -> str:
    s = int(ms / 1000)
    m, s = divmod(s, 60)
    return f"{m}:{s:02d}"

class RandomSong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        client_id = os.environ.get("SPOTID")
        client_secret = os.environ.get("SPOTSEC")
        if not client_id or not client_secret:
            raise RuntimeError("SPOTID and SPOTSEC env vars required")
        self.spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
        self.categories = {
            "top_songs": "top hits",
            "top_of_the_week": "37i9dQZF1DXcBWIGoYBM5M",
            "pop": "37i9dQZF1DXcZDD7cfEKhW",
            "rock": "37i9dQZF1DWXRqgorJj26U",
            "hiphop": "37i9dQZF1DX0XUsuxWHRQd",
            "jazz": "37i9dQZF1DXbITWG1ZJKYt",
            "classical": "37i9dQZF1DWWEJlAGA9gs0",
            "electronic": "37i9dQZF1DX0BcQWzuB7ZO",
            "country": "37i9dQZF1DX1lVhptIYRda",
            "latin": "37i9dQZF1DX10zKzsJ2jva",
            "indie": "37i9dQZF1DX2Nc3B70tvx0",
            "blues": "37i9dQZF1DXd9rSDyQguIk",
        }
        self.max_recent = 40
        self.recent_songs = self._load_recent()
        self.bad_playlists = self._load_bad_playlists()
        self._synced = False
        self.random_song.autocomplete("artist")(self.artist_autocomplete)

    def _load_recent(self):
        try:
            RECENT_FILE.parent.mkdir(parents=True, exist_ok=True)
            if RECENT_FILE.exists():
                with RECENT_FILE.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data[-self.max_recent :]
        except Exception:
            pass
        return []

    def _save_recent(self):
        try:
            with RECENT_FILE.open("w", encoding="utf-8") as f:
                json.dump(self.recent_songs[-self.max_recent :], f)
        except Exception:
            pass

    def _load_bad_playlists(self):
        try:
            BAD_FILE.parent.mkdir(parents=True, exist_ok=True)
            if BAD_FILE.exists():
                with BAD_FILE.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return set(data)
        except Exception:
            pass
        return set()

    def _save_bad_playlists(self):
        try:
            with BAD_FILE.open("w", encoding="utf-8") as f:
                json.dump(list(self.bad_playlists), f)
        except Exception:
            pass

    def _add_bad(self, playlist_id: str):
        if playlist_id:
            self.bad_playlists.add(playlist_id)
            self._save_bad_playlists()

    def _add_recent(self, song_uri: str):
        if song_uri in self.recent_songs:
            try:
                self.recent_songs.remove(song_uri)
            except ValueError:
                pass
        self.recent_songs.append(song_uri)
        if len(self.recent_songs) > self.max_recent:
            self.recent_songs = self.recent_songs[-self.max_recent :]
        self._save_recent()

    async def _get_random_track_from_search(self, query: str, tries_limit: int = 12):
        tries = 0
        while tries < tries_limit:
            offset = random.randint(0, 999)
            try:
                results = self.spotify.search(q=query, type="track", limit=1, offset=offset)
            except Exception:
                return None
            items = results.get("tracks", {}).get("items", [])
            if not items:
                tries += 1
                continue
            track = items[0]
            uri = track.get("uri") or track.get("id")
            if uri and uri not in self.recent_songs:
                return track
            tries += 1
        return None

    async def _choose_track(self, category: str, artist_name: str = None):
        if artist_name:
            try:
                results = self.spotify.search(q=f"artist:{artist_name}", type="track", limit=50)
                tracks = results.get("tracks", {}).get("items", [])
                filtered = [t for t in tracks if t.get("uri") not in self.recent_songs]
                if filtered:
                    return random.choice(filtered)
            except Exception:
                pass
        if category == "top_songs":
            return await self._get_random_track_from_search("top hits")
        if category == "random":
            return await self._get_random_track_from_search("year:2022")
        if category in self.categories:
            return await self._get_random_track_from_search(self.categories[category])
        return await self._get_random_track_from_search("year:2022")

    @commands.Cog.listener()
    async def on_ready(self):
        if self._synced:
            return
        await self.bot.wait_until_ready()
        try:
            await self.bot.tree.sync()  # global sync
            print("Slash commands synced globally.")
        except Exception as e:
            print(f"Failed to sync commands: {e}")
        self._synced = True

    @commands.slash_command(name="random_song", description="Get a random song from Spotify (by genre/category or artist).")
    async def random_song(
        self,
        ctx: discord.ApplicationContext,
        category: discord.Option(str, "Choose category", required=False, choices=["random", *list(["top_songs","top_of_the_week","pop","rock","hiphop","jazz","classical","electronic","country","latin","indie","blues"])], default="random"),
        artist: discord.Option(str, "Search for an artist", required=False, autocomplete=True) = None,
    ):
        await ctx.defer()
        if category == "random":
            category = "random"
        track = await self._choose_track(category, artist)
        if not track:
            await ctx.respond("Couldn't find a new song right now — try again later.", ephemeral=True)
            return
        track_uri = track.get("uri") or f"spotify:track:{track.get('id')}"
        self._add_recent(track_uri)
        track_name = track.get("name", "Unknown")
        artists = ", ".join([a.get("name", "Unknown") for a in track.get("artists", [])])
        album = track.get("album", {}) or {}
        album_name = album.get("name", "Unknown")
        release_date = album.get("release_date", "")
        duration = ms_to_minsec(track.get("duration_ms", 0))
        spotify_url = track.get("external_urls", {}).get("spotify") or f"https://open.spotify.com/track/{track.get('id')}"
        embed = discord.Embed(title=track_name, url=spotify_url, description=f"By {artists}", color=discord.Color.blurple())
        embed.add_field(name="Album", value=album_name, inline=True)
        embed.add_field(name="Duration", value=duration, inline=True)
        if release_date:
            embed.add_field(name="Released", value=release_date, inline=True)
        images = album.get("images") or []
        if images:
            embed.set_thumbnail(url=images[0].get("url"))
        embed.set_footer(text=f"Category: {category.replace('_',' ').title()}")
        view = View()
        view.add_item(Button(label="Open in Spotify", url=spotify_url))
        preview_url = track.get("preview_url")
        if preview_url:
            view.add_item(Button(label="Preview (30s)", url=preview_url))
        await ctx.respond(embed=embed, view=view)

    async def artist_autocomplete(self, interaction: discord.Interaction, current: str):
        if not current:
            return []
        try:
            results = self.spotify.search(q=current, type="artist", limit=10)
            artists = results.get("artists", {}).get("items", [])
            return [
                discord.OptionChoice(name=artist.get("name", "Unknown"), value=artist.get("name", "Unknown"))
                for artist in artists
            ]
        except Exception:
            return []

def setup(bot):
    bot.add_cog(RandomSong(bot))