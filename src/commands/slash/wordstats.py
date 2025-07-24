import discord
from discord.ext import commands
from collections import Counter
import re
from datetime import datetime

class WordStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="wordstats", description="See what words a user uses the most (recent messages across server)")
    async def wordstats(
        self,
        ctx,
        user: discord.Member,
        word: str = None
    ):
        await ctx.defer()

        max_messages = 500
        all_words = []
        total_checked = 0
        timestamps = []

        for channel in ctx.guild.text_channels:
            if not channel.permissions_for(ctx.guild.me).read_message_history:
                continue

            try:
                async for msg in channel.history(limit=500, oldest_first=False):
                    if msg.author.id == user.id and not msg.author.bot:
                        words = re.findall(r"\b\w+\b", msg.content.lower())
                        all_words.extend(words)
                        timestamps.append(msg.created_at)
                        total_checked += 1

                        if total_checked >= max_messages:
                            break
                if total_checked >= max_messages:
                    break
            except discord.Forbidden:
                continue

        if not all_words:
            embed = discord.Embed(
                title="No Data Found",
                description=f"No recent messages found for {user.mention}.",
                color=discord.Color.blurple()
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
            await ctx.respond(embed=embed)
            return

        newest = timestamps[0].strftime('%Y-%m-%d)
        oldest = timestamps[-1].strftime('%Y-%m-%d)
        time_range = f"From **{newest}** to **{oldest}**"

        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_author(name=f"Word Stats for {user.display_name}", icon_url=user.avatar.url)
        embed.set_footer(text=f"{user.display_name}'s message history", icon_url=user.avatar.url)

        if word:
            word = word.lower()
            count = all_words.count(word)
            embed.title = f"'{word}' Usage:"
            embed.description = (
                f"**{user.mention}** said '**{word}**' **{count}** times "
                f"in their **most recent {total_checked} messages**.\n\n{time_range}"
            )
        else:
            counter = Counter(all_words)
            top_words = counter.most_common(10)
            top_text = "\n".join([f"**{i+1}. {w}** — {c} times" for i, (w, c) in enumerate(top_words)])
            embed.title = "Top 10 Words"
            embed.description = (
                f"Analyzed {total_checked} **most recent messages:** from {user.mention}\n{time_range}\n\n{top_text}"
            )

        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(WordStats(bot))