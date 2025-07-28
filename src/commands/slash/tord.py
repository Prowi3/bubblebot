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

    @commands.slash_command(name="truthordare", description="Play a round of Truth or Dare!")
    async def truth_or_dare(self, ctx):
        await ctx.defer()

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
            "Generate a unique, funny, or thought-provoking **truth question** for a truth or dare game. "
            "No repeats, no clichés. Do not include any explanation, just the question."
        )
        question = await fetch_prompt(prompt)
        await interaction.response.send_message(f"**Truth:** {question}", ephemeral=True)

    @discord.ui.button(label="Dare", style=discord.ButtonStyle.success)
    async def dare_button(self, button: Button, interaction: discord.Interaction):
        prompt = (
            "Generate a bold, creative, or funny **dare challenge** suitable for a truth or dare game. "
            "Avoid physical danger or illegal acts. Just the dare, no explanation."
        )
        dare = await fetch_prompt(prompt)
        await interaction.response.send_message(f"**Dare:** {dare}", ephemeral=True)

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