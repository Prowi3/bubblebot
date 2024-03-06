import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import shutil
import asyncio

class Play(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.voice_channel = None
        self.song_finished = False

    @commands.slash_command(name="play_song", description="Download and play a song from a YouTube URL")
    async def play_song(self, ctx: discord.ApplicationContext,
                        url: discord.Option(str, description="YouTube URL of the song to play") = "https://www.youtube.com/watch?v=h-NpsoLlMMA&pp=ygUeY2hpbGwgc2hvcnQgbG9maSBhbWJpZW50IHNvdW5k",
                        channel: discord.Option(discord.VoiceChannel, description="Select the Voice Channel that you want to play the song") = None, 
                        cancel: discord.Option(bool, description="Cancel the song that is Playing if any") = False):

        await ctx.defer()

        if cancel:
            if self.voice_client and self.voice_client.is_playing():
                self.song_finished = False
                self.voice_client.stop()
                await ctx.respond("Song canceled.")
                await self.voice_channel.disconnect()
                self.voice_client = None
                self.voice_channel = None
            else:
                await ctx.respond("No song is currently playing.")
            return

        if channel is None:
            await ctx.respond("Please specify a voice channel.")
            return

        try:
            if self.voice_client is None or not self.voice_client.is_connected():
                self.voice_client = await channel.connect()
                self.voice_channel = channel

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': '%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'ffmpeg_location': shutil.which('ffmpeg'),
                'ffprobe_location': shutil.which('ffprobe'),
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = f"{info['title']}.mp3"

            source = discord.FFmpegPCMAudio(filename)
            self.voice_client.play(source)

            await ctx.respond(f"Bubble is playing ({info['title']}) in {channel.name}.")

            while self.voice_client.is_playing():
                await asyncio.sleep(1)

            if not self.song_finished:
                await ctx.respond("song finished")

            await self.voice_channel.disconnect()
            self.voice_client = None
            self.voice_channel = None
            self.song_finished = True

        except Exception as e:
            await ctx.respond(f"An error occurred: {e}")

def setup(bot):
    bot.add_cog(Play(bot))