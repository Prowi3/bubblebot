import discord
from discord.ext import commands

class Pagination:
    def __init__(self, ctx):
        self.ctx = ctx
        self.pages = []
        self.current_page = 0

    async def send_current_page(self):
        await self.ctx.send(embed=self.pages[self.current_page])

    def add_page(self, embed):
        self.pages.append(embed)

    async def show(self):
        await self.send_current_page()

        async def prev_button_callback(interaction):
            self.current_page = (self.current_page - 1) % len(self.pages)
            await self.send_current_page()

        async def next_button_callback(interaction):
            self.current_page = (self.current_page + 1) % len(self.pages)
            await self.send_current_page()

        prev_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="Previous", custom_id="prev")
        prev_button.callback = prev_button_callback

        next_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="Next", custom_id="next")
        next_button.callback = next_button_callback

        view = discord.ui.View()
        view.add_item(prev_button)
        view.add_item(next_button)

        await self.ctx.send("Use the buttons to navigate.", view=view)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="help", description="BubbleBot's information")
    async def help_slash(self, ctx):
        pagination = Pagination(ctx)

        embed1 = discord.Embed(
            title="BubbleBot Help",
            description="Here's a list of available commands:",
            color=discord.Color(0x9FC6F6)
        )
        thumbnail_url = "https://cdn.discordapp.com/attachments/1142411437688500274/1146230560205840446/output-onlinegiftools_2.gif"
        embed1.set_thumbnail(url=thumbnail_url)

        embed1.add_field(name="__**/cta**__", value="**╰→** Get a random cat picture.")
        embed1.add_field(name="__**/draw_noise**__", value="**╰→** Generate an image using perlin noise with text")
        embed1.add_field(name="__**/pfp**__", value="**╰→** Fetch a user's profile picture.")
        embed1.add_field(name="__**/not_sfw**__", value="**╰→** Get a reandom and *totally family-friendly* picture.")
        embed1.add_field(name="__**/sfw**__", value="**╰→** Get a random safe anime picture.")
        embed1.add_field(name="__**/pet**__", value="**╰→** Pet users, server emotes, or image URLs.")
        embed1.add_field(name="__**BB Search**__", value="**╰→** Search for images from Google.")
        embed1.add_field(name="__**BB Google**__", value="**╰→** High-quality image search (limited to 100 per day).")

        embed1.set_footer(text="1/3")
        pagination.add_page(embed1)

        embed2 = discord.Embed(
            title="/clouds_draw Help",
            description="Here's a list of what each parameter does:",
            color=discord.Color(0xFFFFFF)
        )

        thumbnail_url2 = "https://cdn.discordapp.com/attachments/1142411437688500274/1149559291313922098/New_Project_341_D93B16A.gif"
        embed2.set_thumbnail(url=thumbnail_url2)

        embed2.add_field(name="1- **Octaves**:", value="You can vary the number of octaves to control the level of detail in the noise. Higher octaves create more intricate patterns, Values around 1-10 are recommend.")
        embed2.add_field(name="2- **Lacunarity**:", value="Lacunarity affects the frequency of each successive octave. Increasing it can lead to more variations in the noise.")
        embed2.add_field(name="3- **Persistence**:", value="This parameter controls how much each successive octave contributes to the final noise. Values around 0.5 provide a balanced look, while values above 0.5 emphasize the higher octaves.")
        embed2.add_field(name="4- **Font**:", value="Select your preferred Font")
        embed2.add_field(name="5- **Text**:", value="Whatever you type will appear in the image unless it's some weird characters/emojis")

        embed2.set_footer(text="2/3")
        pagination.add_page(embed2)

        embed3 = discord.Embed(
            title="THAT'S BASICALLY IT!",
            description="If you encounter any issues or want to share something with us, please don't hesitate to get in touch by using (/contact). We're always here to help! :)",
            color=discord.Color(0xF23F43)
        )

        embed3.set_footer(text="3/3")
        pagination.add_page(embed3)

        await pagination.show()

def setup(bot):
    bot.add_cog(Help(bot))