import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import ffmpeg
import shutil

class DlSong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="dl_song", description="Download a song from a YouTube URL")
    async def dl_song(self, ctx, url: str):

        await ctx.defer()

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

        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = f"{info['title']}.mp3"

            with open(filename, "rb") as f:
                await ctx.respond(content="Done!", file=discord.File(f, filename=filename))

        except Exception as e:
            await ctx.respond(f"An error occurred: {e}")

def setup(bot):
    bot.add_cog(DlSong(bot))