import discord
from discord.ext import commands, tasks
import yt_dlp as youtube_dl
import shutil
import asyncio

class Play(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None

    @commands.slash_command(name="play_song", description="Download and play a song from a YouTube URL")
    async def play_song(self, ctx: discord.ApplicationContext,
                        url: str,
                        channel: discord.Option(channel_type=discord.ChannelType.voice, description="Select the Voice Channel that you want to play the song") = None, 
                        play: discord.Option(bool, description="Bubble will join the vc and play the song") = False, 
                        cancel: discord.Option(bool, description="Cancel the song that is Playing if any") = False, 
                        leave: discord.Option(bool, description="Stop the Song and Leave the channel") = False):

        if play:
            if channel is None:
                await ctx.respond("Please specify a voice channel.")
                return
            self.voice_client = await channel.connect()
            await ctx.respond(content="Bubble is Playing a Song Now...")

            try:
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

                while self.voice_client.is_playing():
                    await asyncio.sleep(1)
                
                await self.voice_client.disconnect()
            except Exception as e:
                await ctx.respond(f"An error occurred: {e}")

        elif cancel:
            if self.voice_client and self.voice_client.is_playing():
                self.voice_client.stop()
                await ctx.respond("Song canceled.")
            else:
                await ctx.respond("No song is currently playing.")

        elif leave:
            if self.voice_client and self.voice_client.is_connected():
                await self.voice_client.disconnect()
                await ctx.respond("Bubble left the voice channel.")
            else:
                await ctx.respond("Bubble is not in a voice channel.")

        else:
            await ctx.respond("Please select a valid command: play, cancel, or leave.")

def setup(bot):
    bot.add_cog(Play(bot))