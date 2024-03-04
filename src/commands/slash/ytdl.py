import discord
from discord.ext import commands
from pytube import YouTube

class DlSong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="dl_song", description="Download a song from a YouTube URL")
    async def dl_song(self, ctx, url: str):
        try:
            yt = YouTube(url)
            stream = yt.streams.get_audio_only()
            filename = f"{yt.title}.mp3"
            stream.download(filename=filename)

            with open(filename, "rb") as f:
                await ctx.send(file=discord.File(f))

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

def setup(bot):
    bot.add_cog(DlSong(bot))
