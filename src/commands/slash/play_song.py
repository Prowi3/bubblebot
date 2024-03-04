import discord
from discord.ext import commands
from pytube import YouTube

class PlaySong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice = None

    async def join_vc(self, ctx, vc_name):
        if ctx.voice_client:
            if ctx.voice_client.channel.name == vc_name:
                return
            await ctx.voice_client.move_to(ctx.guild.get_channel(vc_name))
        else:
            self.voice = await ctx.guild.get_channel(vc_name).connect()

    async def leave_vc(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.voice = None

    @commands.slash_command(name="play_song", description="Download a song from a YouTube URL")
    async def play_song(self, ctx, option: str, vc_name: discord.VoiceChannel, url: str):
        if option.lower() == "play":
            await self.join_vc(ctx, vc_name.name)
            await ctx.respond(content=f"Playing in {vc_name.name}...")

            try:
                yt = YouTube(url)
                stream = yt.streams.get_audio_only()
                filename = f"{yt.title}.mp3"
                stream.download(filename=filename)

                with open(filename, "rb") as f:
                    await ctx.respond(content=f"Done! Now playing {yt.title} in {vc_name.name}...", file=discord.File(f, filename=f"{yt.title}.mp3"))

                if ctx.voice_client:
                    ctx.voice_client.play(discord.FFmpegPCMAudio(filename))
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
            await ctx.respond("Please provide a valid voice channel.")

def setup(bot):
    bot.add_cog(PlaySong(bot))