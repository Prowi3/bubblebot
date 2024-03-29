import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import shutil
import asyncio
import os

class Play(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.voice_channel = None

    @commands.slash_command(name="play_song", description="Download and play a song from a YouTube URL")
    async def play_song(self, ctx: discord.ApplicationContext,
                        url: discord.Option(str, description="YouTube URL of the song to play") = "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                        channel: discord.Option(discord.VoiceChannel, description="Select the Voice Channel that you want to play the song") = None, 
                        cancel: discord.Option(bool, description="Cancel the song that is Playing if any") = False):

        await ctx.defer()

        if cancel:
            if self.voice_client and self.voice_client.is_playing():
                self.voice_client.stop()
                await self.voice_client.disconnect()
                self.voice_client = None
                self.voice_channel = None
                await ctx.respond("Song canceled.")
            else:
                await ctx.respond("No song is currently playing.")
            return

        if channel is None:
            await ctx.respond("Please specify a voice channel.")
            return

        try:
            if self.voice_client is not None:
                await self.voice_client.disconnect()
            
            self.voice_client = await channel.connect()
            self.voice_channel = channel

            ydl_opts = {
                'format': 'bestaudio/best[acodec=opus]',
                'outtmpl': '%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'opus',
                    'preferredquality': '192',
                }],
                'ffmpeg_location': shutil.which('ffmpeg'),
                'ffprobe_location': shutil.which('ffprobe'),
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = f"{info['title']}.opus"

            source = discord.FFmpegOpusAudio(filename, executable="ffmpeg", options='-ac 2')
            self.voice_client.play(source)

            await ctx.respond(f"Playing *{info['title']}* in {channel.name}.")

        except Exception as e:
            await ctx.respond(f"An error occurred: {e}")

def setup(bot):
    bot.add_cog(Play(bot))