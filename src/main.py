import os
import discord
import io
import random


from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont


prefix = "bb "

intents = discord.Intents.all()

bot = commands.Bot(prefix, intents=intents, activity=discord.Game(name="Poker"))


@bot.event
async def on_ready():
    os.system("clear")
    print(bot.user)

@bot.command()
async def hello(ctx):
    await ctx.send("Hello !")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.lower() == "poke":
        await message.channel.send("Hey Don't Do That! >:(", reference=message)
    await bot.process_commands(message)

#snakes and ladders


class SnakesAndLaddersGame:
    def __init__(self):
        self.grid_size = 10
        self.square_size = 80
        self.board_size = self.grid_size * self.square_size
        self.players = [0, 0]
        self.snakes = {16: 6, 47: 26, 49: 11, 56: 53, 62: 19, 64: 60, 87: 24, 93: 73, 95: 75, 98: 78}
        self.ladders = {1: 38, 4: 14, 9: 31, 21: 42, 28: 84, 36: 44, 51: 67, 71: 91, 80: 100}
        self.current_player = 0
        self.dice_roll = 0

    def roll_dice(self):
        self.dice_roll = random.randint(1, 6)

    def move_player(self, player_index):
        self.players[player_index] += self.dice_roll
        if self.players[player_index] in self.snakes:
            self.players[player_index] = self.snakes[self.players[player_index]]
        elif self.players[player_index] in self.ladders:
            self.players[player_index] = self.ladders[self.players[player_index]]
        if self.players[player_index] > 100:
            self.players[player_index] = 200 - self.players[player_index]

    def switch_turn(self):
        self.current_player = 1 - self.current_player

    def get_player_position(self, player_index):
        row = self.players[player_index] // self.grid_size
        col = self.players[player_index] % self.grid_size
        return col, self.grid_size - row - 1

    def play_turn(self):
        self.roll_dice()
        self.move_player(self.current_player)
        self.switch_turn()

    def is_game_over(self):
        return any(player >= 100 for player in self.players)

@bot.command()
async def snakes_and_ladders(ctx):
    game = SnakesAndLaddersGame()

    while not game.is_game_over():
        img = Image.new("RGB", (game.board_size, game.board_size), color="white")
        draw = ImageDraw.Draw(img)

        for i in range(game.grid_size):
            for j in range(game.grid_size):
                x = i * game.square_size
                y = (game.grid_size - 1 - j) * game.square_size
                square_coords = (x, y)
                square_end_coords = (x + game.square_size, y + game.square_size)
                draw.rectangle((square_coords, square_end_coords), outline="black", width=3)

        for start, end in game.snakes.items():
            start_x, start_y = game.get_player_position(start)
            end_x, end_y = game.get_player_position(end)
            draw.line([(start_x * game.square_size + game.square_size // 2, start_y * game.square_size + game.square_size // 2),
                       (end_x * game.square_size + game.square_size // 2, end_y * game.square_size + game.square_size // 2)],
                      fill="red", width=5)
        
        for start, end in game.ladders.items():
            start_x, start_y = game.get_player_position(start)
            end_x, end_y = game.get_player_position(end)
            draw.line([(start_x * game.square_size + game.square_size // 2, start_y * game.square_size + game.square_size // 2),
                       (end_x * game.square_size + game.square_size // 2, end_y * game.square_size + game.square_size // 2)],
                      fill="green", width=5)

        for i in range(2):
            player_x, player_y = game.get_player_position(i)
            draw.ellipse([(player_x * game.square_size + game.square_size // 4, player_y * game.square_size + game.square_size // 4),
                         (player_x * game.square_size + 3 * game.square_size // 4, player_y * game.square_size + 3 * game.square_size // 4)],
                         fill="blue" if i == game.current_player else "orange", outline="black", width=3)

        img_path = "snakes_and_ladders.png"
        img.save(img_path)

        await ctx.send("Current game state:", file=discord.File(img_path))
        
        game.play_turn()

    winners = [i + 1 for i, player in enumerate(game.players) if player >= 100]
    if winners:
        winners_text = ", ".join(map(str, winners))
        await ctx.send(f"Player {winners_text} win{'s' if len(winners) > 1 else ''}!")
    else:
        await ctx.send("The game ended in a draw.")
#error log

@bot.event
async def on_command_error(ctx, error):
    channel_id = 1142387860650082334
    chan = bot.get_channel(channel_id)
    
    embed = discord.Embed(
        title=f'Command Error in {ctx.command}',
        description=str(error),
        color=discord.Color(int("0xAA698F", 16))
    )
    
    await chan.send(embed=embed)



bot.run(os.environ["TOKEN"])
