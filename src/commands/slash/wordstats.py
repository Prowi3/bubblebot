import discord
from discord.ext import commands
from collections import Counter
import re
from datetime import datetime

class WordStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="wordstats", description="See what words a user uses the most (last 500 messages/server-wide)")
    async def wordstats(
        self,
        ctx,
        user: discord.Member,
        word: str = None
    ):
        await ctx.defer()
        all_words = []
        total_checked = 0
        timestamps = []

        for channel in ctx.guild.text_channels:
            try:
                messages = await channel.history(limit=500).flatten()
            except discord.Forbidden:
                continue

            for msg in messages:
                if msg.author.id == user.id and not msg.author.bot:
                    cleaned = re.sub(r"[^\w\s]", "", msg.content.lower())
                    words = cleaned.split()
                    all_words.extend(words)
                    timestamps.append(msg.created_at)
                    total_checked += 1

        if not all_words:
            embed = discord.Embed(
                title="No Data Found",
                description=f"No recent messages found for {user.mention}.",
                color=discord.Color.blurple()
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
            await ctx.respond(embed=embed)
            return
          
        time_range = ""
        if timestamps:
            oldest = min(timestamps).strftime('%Y-%m-%d %H:%M')
            newest = max(timestamps).strftime('%Y-%m-%d %H:%M')
            time_range = f"From **{oldest}** to **{newest}** UTC"

        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_author(name=f"Word Stats for {user.display_name}", icon_url=user.avatar.url)
        embed.set_footer(text=f"{user.display_name}'s message history", icon_url=user.avatar.url)

        if word:
            word = word.lower()
            count = all_words.count(word)
            embed.title = f"'{word}' usage"
            embed.description = (
                f"**{user.mention}** said '**{word}**' **{count}** times "
                f"in the last **{total_checked} messages**.\n\n{time_range}"
            )
        else:
            counter = Counter(all_words)
            top_words = counter.most_common(10)
            top_text = "\n".join([f"**{i+1}. {w}** — {c} times" for i, (w, c) in enumerate(top_words)])
            embed.title = "Top 10 Words"
            embed.description = (
                f"Analyzed **{total_checked} messages** from {user.mention}\n{time_range}\n\n{top_text}"
            )

        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(WordStats(bot))