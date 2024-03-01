import discord
from discord.ext import commands
import aiohttp
import re
from io import BytesIO
from petpetgif import petpet as petpetgif

class Pet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="petpet", description="Pet Users, Server Emotes, Or Image Links")
    async def pet(self, ctx, user: discord.Member = None, emote: str = None, image_url: str = None):
        async with aiohttp.ClientSession() as session:
            if user:
                image_data = await user.avatar.read()
            elif emote:
                emote_match = re.match(r'<:(\w+):(\d+)>', emote)
                if emote_match:
                    emote_id = int(emote_match.group(2))
                    emote = discord.utils.get(ctx.guild.emojis, id=emote_id)
                    if emote:
                        image_url = emote.url
                        async with session.get(image_url) as resp:
                            image_data = await resp.read()
                    else:
                        await ctx.respond("Invalid petting :(")
                        return
                else:
                    await ctx.respond("Invalid emote")
                    return
            elif image_url:
                async with session.get(image_url) as resp:
                    image_data = await resp.read()
            else:
                await ctx.respond("Please provide an image URL, mention a user, or an emote to pet.")
                return

            source = BytesIO(image_data)
            dest = BytesIO()
            petpetgif.make(source, dest)
            dest.seek(0)
            await ctx.respond(file=discord.File(dest, filename="petpet.gif"))

def setup(bot):
    bot.add_cog(Pet(bot))
