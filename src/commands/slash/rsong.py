import discord
import os
import json
import random
from pathlib import Path
from discord.ext import commands
from discord.ui import View, Button
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from io import BytesIO
from PIL import Image
import aiohttp

RECENT_FILE = Path("data/recent_songs.json")
BAD_FILE = Path("data/bad_playlists.json")

def ms_to_minsec(ms: int) -> str:
    s = int(ms / 1000)
    m, s = divmod(s, 60)
    return f"{m}:{s:02d}"

async def get_dominant_color(url: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return discord.Color.blurple()
                data = await resp.read()
        img = Image.open(BytesIO(data)).convert("RGB").resize((50, 50))
        pixels = list(img.getdata())
        r = sum([p[0] for p in pixels]) // len(pixels)
        g = sum([p[1] for p in pixels]) // len(pixels)
        b = sum([p[2] for p in pixels]) // len(pixels)
        return discord.Color.from_rgb(r, g, b)
    except Exception:
        return discord.Color.blurple()

class RandomSong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        client_id = os.environ.get("SPOTID")
        client_secret = os.environ.get("SPOTSEC")
        if not client_id or not client_secret:
            raise RuntimeError("SPOTID and SPOTSEC env vars required")
        self.spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
        self.categories = {
            "top_of_the_week": "37i9dQZF1DXcBWIGoYBM5M",    # Today's Top Hits
            "pop": "37i9dQZF1DXcZDD7cfEKhW",                  # Pop Rising
            "rock": "37i9dQZF1DWXRqgorJj26U",                 # Rock This
            "hiphop": "37i9dQZF1DX0XUsuxWHRQd",               # RapCaviar
            "jazz": "37i9dQZF1DXbITWG1ZJKYt",                 # Jazz Classics
            "classical": "37i9dQZF1DWWEJlAGA9gs0",            # Classical Essentials
            "electronic": "37i9dQZF1DX0BcQWzuB7ZO",           # Mint
            "country": "37i9dQZF1DX1lVhptIYRda",               # Hot Country
            "latin": "37i9dQZF1DX10zKzsJ2jva",                 # Viva Latino
            "indie": "37i9dQZF1DX2Nc3B70tvx0",                 # Indie Pop
            "blues": "37i9dQZF1DXd9rSDyQguIk",                 # Blues Classics
        }
        self.max_recent = 40
        self.recent_songs = self._load_recent()
        self.bad_playlists = self._load_bad_playlists()
        self._validate_and_prune_playlists()
        self._synced = False

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

    def _is_playlist_id(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        if " " in value:
            return False
        if len(value) < 10:
            return False
        return True

    def _validate_and_prune_playlists(self):
        to_remove = []
        for key, source in list(self.categories.items()):
            if not self._is_playlist_id(source):
                continue
            if source in self.bad_playlists:
                to_remove.append(key)
                continue
            try:
                self.spotify.playlist(source)
            except Exception:
                self._add_bad(source)
                to_remove.append(key)
        for key in to_remove:
            self.categories.pop(key, None)

    async def _get_random_track_from_playlist(self, playlist_id: str, tries_limit: int = 12):
        if not playlist_id or playlist_id in self.bad_playlists:
            return None
        try:
            playlist = self.spotify.playlist(playlist_id)
            total_tracks = playlist.get("tracks", {}).get("total", 0)
        except Exception:
            self._add_bad(playlist_id)
            return None
        if total_tracks <= 0:
            return None
        tries = 0
        while tries < tries_limit:
            safe_max = min(total_tracks - 1, 9999)
            offset = random.randint(0, safe_max)
            try:
                items = self.spotify.playlist_items(playlist_id, limit=1, offset=offset, additional_types=("track",))
            except Exception:
                self._add_bad(playlist_id)
                return None
            if not items or not items.get("items"):
                tries += 1
                continue
            item = items["items"][0].get("track") or items["items"][0]
            if not item:
                tries += 1
                continue
            track = item
            uri = track.get("uri") or track.get("id")
            if not uri:
                tries += 1
                continue
            if uri not in self.recent_songs:
                return track
            tries += 1
        return None

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
        if category == "random":
            return await self._get_random_track_from_search("year:2022")
        if category in self.categories:
            playlist_id = self.categories[category]
            track = await self._get_random_track_from_playlist(playlist_id)
            if track:
                return track
            # fallback to search if playlist failed
            return await self._get_random_track_from_search(category)
        return await self._get_random_track_from_search("year:2022")

    @commands.Cog.listener()
    async def on_ready(self):
        if self._synced:
            return
        try:
            await self.bot.wait_until_ready()
            await self.bot.tree.sync()
        except Exception:
            pass
        self._synced = True

    @commands.slash_command(name="random_song", description="Get a random song from Spotify (by genre/category or artist).")
    async def random_song(
        self,
        ctx,
        category: discord.Option(
            str,
            "Choose category or genre",
            required=False,
            choices=list(self.categories.keys()) + ["random"],
        ) = "random",
        artist: discord.Option(str, "Search for an artist", required=False) = None,
    ):
        await ctx.defer()
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
        images = album.get("images") or []
        color = discord.Color.blurple()
        if images:
            color = await get_dominant_color(images[0].get("url"))

        embed = discord.Embed(title=track_name, url=spotify_url, description=f"By {artists}", color=color)
        embed.add_field(name="Album", value=album_name, inline=True)
        embed.add_field(name="Duration", value=duration, inline=True)
        if release_date:
            embed.add_field(name="Released", value=release_date, inline=True)
        if images:
            embed.set_thumbnail(url=images[0].get("url"))
        embed.set_footer(text=f"Category: {category.replace('_',' ').title()}")

        view = View()
        view.add_item(Button(label="Open in Spotify", url=spotify_url))
        preview_url = track.get("preview_url")
        if preview_url:
            view.add_item(Button(label="Preview (30s)", url=preview_url))

        await ctx.respond(embed=embed, view=view)

    @random_song.autocomplete("artist")
    async def artist_autocomplete(self, ctx: discord.AutocompleteContext, user_input: str):
        if not user_input:
            return []
        try:
            results = self.spotify.search(q=user_input, type="artist", limit=10)
            artists = results.get("artists", {}).get("items", [])
            return [
                discord.OptionChoice(name=artist.get("name", "Unknown"), value=artist.get("name", "Unknown"))
                for artist in artists
            ]
        except Exception:
            return []

def setup(bot):
    bot.add_cog(RandomSong(bot))