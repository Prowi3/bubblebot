import discord
from discord.ext import commands
from discord.ui import Modal, InputText

class TextModal(Modal):
    def __init__(self):
      super().__init__(title="Enter Text", custom_id="text_modal_id")
      self.text_input = InputText(label="Your Text", style=discord.InputTextStyle.long, custom_id="text_content")
      self.add_item(self.text_input)

async def callback(self, interaction):
    text = self.text_input.value
    try:
        await interaction.channel.respond(f"You entered: {text}")
    except discord.HTTPException as e:
        await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

class Silly(commands.Cog):
    def __init__(self, bot):
      self.bot = bot

    @commands.slash_command(name="silly", description="Get text input from user")
    async def text_command(self, ctx):
        await ctx.interaction.response.send_modal(TextModal())

def setup(bot):
  bot.add_cog(Silly(bot))
