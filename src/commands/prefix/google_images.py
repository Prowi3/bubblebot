import os
import random
import discord
from discord.ext import commands
from googleapiclient.discovery import build

sent_image_links = []

@commands.command(name="gl", aliases=["google"])
async def google_images(ctx, *, query: str):
    global sent_image_links

    service = build("customsearch", "v1", developerKey=os.environ['GLSEARCH'])
    results = service.cse().list(
        q=query,
        cx='779432b9c976d4325',
        searchType='image',
        safe='high'
    ).execute()

    if 'items' in results and len(results['items']) > 0:
        image_links = [item['link'] for item in results['items']]
        
        new_image_links = [link for link in image_links if link not in sent_image_links]
        
        if not new_image_links:
            await ctx.send("No new images found.")
            return

        random_image_link = random.choice(new_image_links)
        sent_image_links.append(random_image_link)
        
        embed = discord.Embed(title=f"You searched for: {query}", color=0x9FC6F6)
        embed.set_image(url=random_image_link)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("Stop searching for weird shit please")

def setup(bot):
    bot.add_command(google_images)