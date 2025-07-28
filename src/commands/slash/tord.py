import discord
from discord.ext import commands
from discord.ui import View, Button
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.environ["GPTKEY"])

class TruthOrDare(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="tod", description="Play a round of Truth or Dare!")
    async def truth_or_dare(self, ctx):
        embed = discord.Embed(
            title="🎲 Truth or Dare",
            description="Click a button to get a challenge!",
            color=0x9FC6F6
        )
        view = TruthOrDareView()
        await ctx.respond(embed=embed, view=view)

class TruthOrDareView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Truth", style=discord.ButtonStyle.primary)
    async def truth_button(self, button: Button, interaction: discord.Interaction):
        prompt = (
            "Generate a creative, funny, or thought-provoking truth question for a truth or dare game. "
            "Avoid general or hypothetical questions like 'If you could...' or 'what animal would you be'. "
            "Make it feel social, emotional, or personal. Just the question. No explanation."
        )
        question = await fetch_prompt(prompt)
        embed = discord.Embed(
            title="🎲 Truth or Dare",
            description=f"**Truth:** {question}",
            color=0x9FC6F6
        )
        await interaction.response.send_message(embed=embed, view=TruthOrDareView())

    @discord.ui.button(label="Dare", style=discord.ButtonStyle.success)
    async def dare_button(self, button: Button, interaction: discord.Interaction):
        prompt = (
            "Generate a realistic, funny, or slightly embarrassing dare that someone can actually perform in a Discord chat. "
            "Examples: send a funny message, tag someone, type backwards, speak like a pirate, etc. "
            "Avoid physical dares, absurd things, or anything inappropriate. Just the dare. No explanation."
        )
        dare = await fetch_prompt(prompt)
        embed = discord.Embed(
            title="🎲 Truth or Dare",
            description=f"**Dare:** {dare}",
            color=0x9FC6F6
        )
        await interaction.response.send_message(embed=embed, view=TruthOrDareView())

async def fetch_prompt(prompt: str) -> str:
    try:
        messages = [{"role": "user", "content": prompt}]
        response = client.chat.completions.create(
            model="gemma2-9b-it",
            messages=messages,
            max_tokens=100,
            temperature=1.0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

def setup(bot):
    bot.add_cog(TruthOrDare(bot))