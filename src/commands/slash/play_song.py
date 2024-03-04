import discord
from discord.ext import commands
import youtube_dl

class PlaySong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="play_song", description="Play songs in a voice channel")
    async def play_song(self, ctx, option: str, voice_channel: discord.VoiceChannel, song_url: str = None):
        if not voice_channel.permissions_for(ctx.guild.me).connect or not voice_channel.permissions_for(ctx.guild.me).speak:
            await ctx.send("I don't have permission to join or speak in the selected voice channel.")
            return

        if option.lower() == "play":
            if not ctx.voice_client or ctx.voice_client.channel != voice_channel:
                vc = await voice_channel.connect()
            else:
                vc = ctx.voice_client

            if song_url:
                if vc.is_playing():
                    vc.stop()

                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(song_url, download=False)
                    url = info['formats'][0]['url']
                    vc.play(discord.FFmpegPCMAudio(url))

        elif option.lower() == "cancel":
            if ctx.voice_client and ctx.voice_client.channel == voice_channel and ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            else:
                await ctx.send("No song is currently playing in the specified voice channel.")

        elif option.lower() == "leave":
            if ctx.voice_client and ctx.voice_client.channel == voice_channel:
                await ctx.voice_client.disconnect()
            else:
                await ctx.send("Bubble is not currently in the specified voice channel.")

        else:
            await ctx.send("Invalid option. Available options are: play, cancel, leave")

def setup(bot):
    bot.add_cog(PlaySong(bot))
