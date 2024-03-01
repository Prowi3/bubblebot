import random

async def bubble_call(message):
    if message.content.lower() == "bubble":
        await message.channel.send("GUH!!!!", reference=message)

async def poke(message):
    if message.content.lower() == "poke":
        with open("miscellaneous/text files/poke.txt", "r") as file:
            content = file.read()
            all_lines = content.splitlines()
            output = random.choice(all_lines) 
        await message.channel.send(output, reference=message)

async def mentions(message):
    if message.content.lower() == "<@1131529056882524212>":
        await message.channel.send("RAAAAAAAAAH!!!!", reference=message)
