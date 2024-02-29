import httpx
from discord.ext import commands

@commands.slash_command(name="cta", description="Send a random cta picture")
async def random_cat(ctx):
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.thecatapi.com/v1/images/search")
        if response.status_code == 200:
            data = response.json()
            cta_url = data[0]["url"]
            await ctx.send(content=cta_url)
        else:
            await ctx.send("Failed to find cta :(")