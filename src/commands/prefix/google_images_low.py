import discord
import requests
import urllib.parse
import random
from bs4 import BeautifulSoup
from discord.ext import commands

sent_image_links = []

@commands.command(name="ser", aliases=["search"])
async def google_images_low(ctx, *, search_query: str):
    search_query_encoded = urllib.parse.quote(search_query)
    search_url = f"https://www.google.com/search?q={search_query_encoded}&tbm=isch&safe=active"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    img_tags = soup.find_all("img")

    image_links = [img["src"] for img in img_tags if "src" in img.attrs and img["src"] not in sent_image_links and not img["src"].endswith(".gif")]

    if image_links:
        selected_image_link = random.choice(image_links)
        sent_image_links.append(selected_image_link)

        search_query_decoded = urllib.parse.unquote(search_query)
        embed = discord.Embed(color=0x9FC6F6, title=f"You searched for: {search_query_decoded}")
        embed.set_image(url=selected_image_link)

        await ctx.send(embed=embed)
    else:
        await ctx.send("No suitable images found.")

def setup(bot):
    bot.add_command(google_images_low)
