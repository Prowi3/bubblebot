import discord
from discord.ext import commands
from pytube import YouTube
import asyncio

class PlaySong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice = None

    async def join_vc(self, ctx, vc_id):
        try:
            channel = self.bot.get_channel(vc_id)
            if channel:
                self.voice = await channel.connect()
        except Exception as e:
            print(f"Error joining voice channel: {e}")

    async def leave_vc(self, ctx):
        try:
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
                self.voice = None
        except Exception as e:
            print(f"Error leaving voice channel: {e}")

    @commands.slash_command(name="play_song", description="Download a song from a YouTube URL")
    async def play_song(self, ctx, option: str, vc_id: int, url: str):
        if option.lower() == "play":
            try:
                await self.join_vc(ctx, vc_id)
                await ctx.respond(content=f"Playing in <#{vc_id}>...")

                yt = YouTube(url)
                stream = yt.streams.get_audio_only()
                filename = f"{yt.title}.mp3"
                stream.download(filename=filename)

                if ctx.voice_client:
                    ctx.voice_client.play(discord.FFmpegPCMAudio(filename))

                await asyncio.sleep(5)

                with open(filename, "rb") as f:
                    await ctx.respond(content=f"Done! Now playing {yt.title} in <#{vc_id}>...", file=discord.File(f, filename=f"{yt.title}.mp3"))

            except Exception as e:
                await ctx.respond(f"An error occurred: {e}")

        elif option.lower() == "cancel":
            if ctx.voice_client and ctx.voice_client.is_playing():
                ctx.voice_client.stop()
                await ctx.respond(content="Song stopped.")
            else:
                await ctx.respond(content="No song is currently playing.")

        elif option.lower() == "leave":
            await self.leave_vc(ctx)
            await ctx.respond(content="Left the voice channel.")

        else:
            await ctx.respond(content="Invalid option. Available options: play, cancel, leave")

    @play_song.error
    async def play_song_error(self, ctx, error):
        if isinstance(error, commands.ChannelNotFound):
            await ctx.respond("Please provide a valid voice channel ID.")

def setup(bot):
    bot.add_cog(PlaySong(bot))