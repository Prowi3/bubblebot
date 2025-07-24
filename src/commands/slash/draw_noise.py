import discord
from discord.ext import commands
from discord import Option
from collections import Counter
import re
import os

class WordStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stopwords = self.load_stopwords("miscellaneous/stopwords.txt")

    def load_stopwords(self, filepath):
        if not os.path.isfile(filepath):
            print(f"Stopword file not found at {filepath}. Using empty list.")
            return set()
        with open(filepath, "r", encoding="utf-8") as f:
            return set(line.strip().lower() for line in f if line.strip())

    @commands.slash_command(
        name="wordstats",
        description="See what words a user uses the most (recent messages across server)"
    )
    async def wordstats(
        self,
        ctx,
        user: Option(discord.Member, "The user to analyze"),
        word: Option(str, "Specific word to count", required=False) = None
    ):
        await ctx.defer()

        max_messages = 500
        collected = 0
        all_words = []
        timestamps = []

        def clean_word(w):
            return (
                len(w) > 1 and
                not w.isdigit() and
                w not in self.stopwords
            )

        emoji_pattern = re.compile(r'<a?:\w+:\d+>')
        word_pattern = re.compile(r'\b\w+\b')

        for channel in ctx.guild.text_channels:
            if not channel.permissions_for(ctx.guild.me).read_message_history:
                continue

            try:
                async for msg in channel.history(limit=1000, oldest_first=False):
                    if msg.author.id == user.id and not msg.author.bot:
                        text = emoji_pattern.sub('', msg.content)
                        words = [w for w in word_pattern.findall(text.lower()) if clean_word(w)]
                        if words:
                            all_words.extend(words)
                            timestamps.append(msg.created_at)
                            collected += 1
                        if collected >= max_messages:
                            break
                if collected >= max_messages:
                    break
            except discord.Forbidden:
                continue

        if not all_words or not timestamps:
            embed = discord.Embed(
                title="No Data Found",
                description=f"No recent messages found for {user.mention}.",
                color=discord.Color.blurple()
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
            await ctx.respond(embed=embed)
            return

        newest = max(timestamps).strftime('%Y-%m-%d')
        oldest = min(timestamps).strftime('%Y-%m-%d')
        time_range = f"From **{oldest}** to **{newest}**"

        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_author(name=f"Word Stats for {user.display_name}", icon_url=user.avatar.url)
        embed.set_footer(text=f"{user.display_name}'s message history", icon_url=user.avatar.url)

        if word:
            word = word.lower()
            count = all_words.count(word)
            embed.title = f"'{word}' Usage:"
            embed.description = (
                f"**{user.mention}** said '**{word}**' **{count}** times "
                f"in their **most recent {collected} messages**.\n\n{time_range}"
            )
        else:
            counter = Counter(all_words)
            top_words = counter.most_common(10)
            top_text = "\n".join([f"**{i+1}. {w}** — {c} times" for i, (w, c) in enumerate(top_words)])
            embed.title = "Top 10 Words"
            embed.description = (
                f"Analyzed {collected} **most recent messages** from {user.mention}\n"
                f"{time_range}\n\n{top_text}"
            )

        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(WordStats(bot))