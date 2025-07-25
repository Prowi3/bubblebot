import discord
from discord.ext import commands

class PrevButton(discord.ui.Button):
    def __init__(self, paginate):
        super().__init__(style=discord.ButtonStyle.secondary, label="Previous", custom_id="prev_button")
        self.paginate = paginate

    async def callback(self, interaction):
        self.paginate.current_page = max(0, self.paginate.current_page - 1)
        
        if self.paginate.current_page < 2:
            self.paginate.next_button.style = discord.ButtonStyle.success
        
        await self.paginate.update_page(self.paginate.current_page, interaction.message)
        await interaction.response.defer()

class NextButton(discord.ui.Button):
    def __init__(self, paginate):
        super().__init__(style=discord.ButtonStyle.success, label="Next", custom_id="next_button")
        self.paginate = paginate

    async def callback(self, interaction):
        self.paginate.current_page = min(len(self.paginate.pages) - 1, self.paginate.current_page + 1)
        
        if self.paginate.current_page == 3:
            self.style = discord.ButtonStyle.danger
        else:
            self.style = discord.ButtonStyle.success
        
        await self.paginate.update_page(self.paginate.current_page, interaction.message)
        await interaction.response.defer()

class Paginate:
    def __init__(self, ctx):
        self.pages = ["", "", "", ""]  # 4 pages now
        self.current_page = 0
        self.ctx = ctx
        self.prev_button = PrevButton(self)
        self.next_button = NextButton(self)
        self.view = discord.ui.View()
        self.view.add_item(self.prev_button)
        self.view.add_item(self.next_button)

    async def update_page(self, page, message):
        page_dict = eval(self.pages[page])
        embed = discord.Embed.from_dict(page_dict)
        await message.edit(embed=embed, view=self.view)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="help", description="BubbleBot's information")
    async def help_slash(self, ctx):
        p = Paginate(ctx)

        # Page 1
        embed1 = discord.Embed(
            title="BubbleBot Help",
            description="Here's a list of available commands:",
            color=discord.Color(0x9FC6F6)
        )
        thumbnail_url = "https://cdn.discordapp.com/attachments/1142411437688500274/1146230560205840446/output-onlinegiftools_2.gif"
        embed1.set_thumbnail(url=thumbnail_url)

        embed1.add_field(name="/__**cta**__", value="**╰→** Get a Random image of a Cat")
        embed1.add_field(name="/__**draw_noise**__", value="**╰→** Create a picture with text by using random noise.")
        embed1.add_field(name="/__**help**__", value="**╰→** This command Will show this message")
        embed1.add_field(name="/__**petpet**__", value="**╰→** Use this Command to Pet User PFPs, Server emotes, or Image URLs")
        embed1.add_field(name="/__**pfp**__", value="**╰→** Get the Profile Picture of the Selected Member")
        embed1.add_field(name="/__**random_song**__", value="**╰→** Get a Random Song from Spotify")
        embed1.add_field(name="/__**wordstats**__", value="**╰→** Analyze and display the most used words by a user from recent messages.")
        embed1.add_field(name="/__**question**__", value="**╰→**Get a random question.")

        embed1.set_footer(text="1/4")

        p.pages[0] = str(embed1.to_dict())

        # Page 2
        embed_prefix = discord.Embed(
            title="Prefix Commands",
            description="These commands use the classic `!` prefix:",
            color=discord.Color(0xFFD700)
        )
        embed_prefix.add_field(name="**bb ser/search**", value="**╰→** Search for any image.", inline=False)
        embed_prefix.add_field(name="**bb gl/google**", value="**╰→** same as search but better", inline=False)
        embed_prefix.add_field(name="**bb test**", value="**╰→** check if the bot is working or not", inline=False)
        embed_prefix.set_footer(text="2/4")

        p.pages[1] = str(embed_prefix.to_dict())

        # Page 3
        embed2 = discord.Embed(
            title="/draw_noise Help",
            description="Here's a list of what each Option does:",
            color=discord.Color(0xFFFFFF)
        )

        thumbnail_url2 = "https://cdn.discordapp.com/attachments/1142411437688500274/1149559291313922098/New_Project_341_D93B16A.gif"
        embed2.set_thumbnail(url=thumbnail_url2)

        embed2.add_field(name="1- **Font**:", value="Select your favorite Font")
        embed2.add_field(name="2- **Text**:", value="Anything you type will show up in the image. You can also use '/' to separate lines example = 'Bubble/Bot' (Emojis and emotes won't work)")
        embed2.add_field(name="3- **Octaves**:", value="You can vary the number of octaves to control the level of detail in the noise. Higher octaves create more intricate patterns, Values around 1-10 are recommend.")
        embed2.add_field(name="4- **Lacunarity**:", value="Lacunarity affects the frequency of each successive octave. Increasing it can lead to more variations in the noise.")
        embed2.add_field(name="5- **Persistence**:", value="This parameter controls how much each successive octave contributes to the final noise. Values around 0.5 provide a balanced look, while values above 0.5 emphasize the higher octaves.")

        embed2.set_footer(text="3/4")
        p.pages[2] = str(embed2.to_dict())

        # Page 4
        embed3 = discord.Embed(
            title="THAT'S BASICALLY IT!",
            description="If you encounter any issues or want to share something with us, please don't hesitate to get in touch by using (/contact). We're always here to help! :)",
            color=discord.Color(0xF23F43)
        )

        embed3.set_footer(text="4/4")
        p.pages[3] = str(embed3.to_dict())

        message = await ctx.respond(embed=embed1)

        view = discord.ui.View()
        view.add_item(PrevButton(p))
        view.add_item(NextButton(p))

        await message.edit_original_response(view=view)

def setup(bot):
    bot.add_cog(Help(bot))