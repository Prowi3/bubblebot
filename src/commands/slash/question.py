import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.environ["GPTKEY"])

class Question(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="question", description="Get a random question.")
    async def question(self, ctx):
        await ctx.defer()

        prompt = "Generate a single creative, funny, or thought-provoking question. Avoid repeating topics or structures used in previous questions. Do NOT use 'If animals could...' or any similar phrasing repeatedly. Do not include any explanations or intros—just the question itself. Make the question sound fresh and unique each time."

        messages = [
            {"role": "user", "content": prompt}
        ]

        try:
            response = client.chat.completions.create(
                model="gemma2-9b-it",
                messages=messages,
                max_tokens=100,
                temperature=1.0,
            )
            question_text = response.choices[0].message.content.strip()
            await ctx.respond(question_text)

        except Exception as e:
            await ctx.respond(f"Error: `{e}`")

def setup(bot):
    bot.add_cog(Question(bot))