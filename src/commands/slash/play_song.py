import discord
from discord.ext import commands
import asyncio
import yt_dlp

class PlaySong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="play_song", description="Play songs in a voice channel")
    async def play_song(self, ctx, option: str, voice_channel: discord.VoiceChannel, song_url: str = None):
        if not voice_channel.permissions_for(ctx.guild.me).connect or not voice_channel.permissions_for(ctx.guild.me).speak:
            await ctx.respond("I don't have permission to join or speak in the selected voice channel.")
            return

        if option.lower() == "play":
            if not ctx.voice_client or ctx.voice_client.channel != voice_channel:
                vc = await voice_channel.connect()
            else:
                vc = ctx.voice_client

            if song_url:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'extractaudio': True,
                    'audioformat': 'mp3',
                    'outtmpl': '%(id)s',
                    'noplaylist': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(song_url, download=False)
                    url = info['url']

                vc.play(discord.FFmpegOpusAudio(url))

        elif option.lower() == "cancel":
            if ctx.voice_client and ctx.voice_client.channel == voice_channel and ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            else:
                await ctx.respond("No song is currently playing in the specified voice channel.")

        elif option.lower() == "leave":
            if ctx.voice_client and ctx.voice_client.channel == voice_channel:
                await ctx.voice_client.disconnect()
            else:
                await ctx.respond("Bot is not currently in the specified voice channel.")

        else:
            await ctx.respond("Invalid option. Available options are: play, cancel, leave")

def setup(bot):
    bot.add_cog(PlaySong(bot))