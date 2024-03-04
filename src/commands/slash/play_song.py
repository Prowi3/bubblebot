import discord
from discord.ext import commands
from pytube import YouTube
import asyncio
import os

class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="play", description="Play a song from a YouTube URL")
    async def play_song(self, ctx, url: str, channel: discord.VoiceChannel):
        try:
            yt = YouTube(url)
            stream = yt.streams.filter(only_audio=True).first()
            filename = f"{yt.title}.mp3"
            stream.download(output_path="audio/", filename=filename)

            voice_client = await channel.connect()

            if voice_client.is_playing():
                voice_client.stop()

            audio_source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"audio/{filename}"))
            voice_client.play(audio_source)

            while voice_client.is_playing():
                await asyncio.sleep(1)

            await voice_client.disconnect()

            os.remove(f"audio/{filename}")

        except Exception as e:
            await ctx.respond(f"An error occurred: {e}")

def setup(bot):
    bot.add_cog(MusicPlayer(bot))