from discord.ext import commands
import httpx

class RandomCat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="cta", description="Get a random cat picture")
    async def random_cat(self, ctx):
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.thecatapi.com/v1/images/search")
            if response.status_code == 200:
                data = response.json()
                cat_url = data[0]["url"]
                await ctx.respond(content=cat_url)
            else:
                await ctx.respond("Failed to find cat :(")

def setup(bot):
    bot.add_cog(RandomCat(bot))
