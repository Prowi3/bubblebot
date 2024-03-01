from discord.ext import commands
import httpx

@commands.slash_command(name="cta", description="Send a random cat picture")
async def random_cat(ctx):
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.thecatapi.com/v1/images/search")
        if response.status_code == 200:
            data = response.json()
            cat_url = data[0]["url"]
            await ctx.send(content=cat_url)
        else:
            await ctx.send("Failed to find cat :(")

def setup(bot):
    bot.add_command(random_cat)
