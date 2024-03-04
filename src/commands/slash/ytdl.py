import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import ffmpeg

class DlSong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="dl_song", description="Download a song from a YouTube URL")
    async def dl_song(self, ctx, url: str):
        await ctx.respond(content="Downloading...")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = f"{info['title']}.mp3"

            ffmpeg.input(filename).output(f"{info['title']}.mp3").run(overwrite_output=True)

            with open(f"{info['title']}.mp3", "rb") as f:
                await ctx.send(content="Done!", file=discord.File(f, filename=f"{info['title']}.mp3"))

        except Exception as e:
            await ctx.respond(f"An error occurred: {e}")

def setup(bot):
    bot.add_cog(DlSong(bot))
