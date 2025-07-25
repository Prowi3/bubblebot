def setup(bot):
    bot.add_cog(WordStats(bot))import discord
from discord.ext import commands
from discord.commands import Option
from collections import Counter, defaultdict
import re
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, timezone

class WordStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("[WordStats] Cog loaded!")

        self.stopwords = self.load_stopwords("miscellaneous/text files/stopwords.txt")
        self.word_pattern = re.compile(r"\b[a-zA-Z']+\b")

    def load_stopwords(self, filepath):
        if not os.path.isfile(filepath):
            return set()
        with open(filepath, "r", encoding="utf-8") as f:
            return set(line.strip().lower() for line in f if line.strip())

    def clean_word(self, word):
        word = word.lower()
        if len(word) <= 1:
            return False
        if any(char.isdigit() for char in word):
            return False
        if word in self.stopwords:
            return False
        if all(c == '_' for c in word):
            return False
        return True

    def generate_trend_image(self, timestamps, username):
        daily_counts = defaultdict(int)
        for ts in timestamps:
            daily_counts[ts.date()] += 1

        sorted_days = sorted(daily_counts)
        counts = [daily_counts[day] for day in sorted_days]

        if not sorted_days:
            return None

        plt.figure(figsize=(10, 4))
        plt.plot(sorted_days, counts, marker='o', linestyle='-', color='skyblue')
        plt.fill_between(sorted_days, counts, color='skyblue', alpha=0.3)
        plt.title(f"{username}'s Message Activity Over Time")
        plt.xlabel("Date")
        plt.ylabel("Messages")
        plt.xticks(rotation=45)
        plt.tight_layout()

        image_path = "trend.png"
        plt.savefig(image_path)
        plt.close()
        return image_path

    @commands.slash_command(
        name="wordstats",
        description="Analyze and display the most used words by a user in a specific channel."
    )
    async def wordstats(
        self,
        ctx,
        user: Option(discord.Member, "The user to analyze"),
        channel: Option(discord.TextChannel, "Channel to analyze"),
        word: Option(str, "Specific word to count", required=False) = None,
        days: Option(int, "How many past days to analyze (default 30)", required=False) = 30
    ):
        await ctx.defer()

        since_time = datetime.now(timezone.utc) - timedelta(days=days)
        word_data = []
        timestamps = []

        perms = channel.permissions_for(ctx.guild.me)
        if not perms.read_message_history:
            return await ctx.respond("❌ I don't have permission to read message history in that channel.", ephemeral=True)

        max_msgs = 10000
        collected_msgs = 0
        max_relevant = 500

        try:
            async for msg in channel.history(limit=max_msgs, after=since_time, oldest_first=False):
                if msg.author.id != user.id or msg.author.bot or not msg.content.strip():
                    continue

                words_raw = self.word_pattern.findall(msg.content)
                words = [w for w in words_raw if self.clean_word(w)]

                if words:
                    timestamps.append(msg.created_at)
                    for w in words:
                        word_data.append((msg.created_at, w))
                    collected_msgs += 1

                if collected_msgs >= max_relevant:
                    break

        except discord.Forbidden:
            return await ctx.respond("❌ I was denied access to that channel.", ephemeral=True)

        if not word_data:
            embed = discord.Embed(
                title="No Data Found",
                description=f"No recent messages found for {user.mention} in {channel.mention}.",
                color=discord.Color(0x9FC6F6)
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            return await ctx.respond(embed=embed)

        word_data.sort(key=lambda x: x[0], reverse=True)
        word_data = word_data[:max_relevant]
        recent_words = [w for _, w in word_data]
        recent_timestamps = [ts for ts, _ in word_data]
        collected = len(recent_words)

        newest = max(recent_timestamps).strftime('%Y-%m-%d')
        oldest = min(recent_timestamps).strftime('%Y-%m-%d')
        time_range = f"From **{oldest}** to **{newest}**"

        embed = discord.Embed(color=discord.Color(0x9FC6F6))
        embed.set_author(name=f"Word Stats for {user.display_name}", icon_url=user.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")

        if word:
            cleaned_word = word.lower().strip()
            count = recent_words.count(cleaned_word)
            embed.title = f"'{cleaned_word}' Usage:"
            embed.description = (
                f"**{user.mention}** said '**{cleaned_word}**' **{count}** times "
                f"in their **most recent {collected} messages** in {channel.mention}.\n\n{time_range}"
            )
        else:
            counter = Counter(recent_words)
            top_words = counter.most_common(10)
            if not top_words:
                embed.title = "No Common Words Found"
                embed.description = "No frequent words detected after filtering stopwords."
            else:
                top_text = "\n".join([f"**{i+1}. {w}** — {c} times" for i, (w, c) in enumerate(top_words)])
                embed.title = f"Top 10 Words in {channel.name}"
                embed.description = (
                    f"Analyzed {collected} messages from {user.mention} in {channel.mention}\n"
                    f"{time_range}\n\n{top_text}"
                )

        image_path = self.generate_trend_image(recent_timestamps, user.display_name)
        if image_path and os.path.isfile(image_path):
            file = discord.File(image_path, filename="trend.png")
            embed.set_image(url="attachment://trend.png")
            await ctx.respond(embed=embed, file=file)
        else:
            await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(WordStats(bot))