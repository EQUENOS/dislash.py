# will remove in production
import dislash
import discord
from discord.ext import commands

bot = commands.Bot('!')
client = dislash.InteractionClient(bot, test_guilds=[570841314200125460])

@bot.event
async def on_ready():
    print('ready')

@client.slash_command()
async def command(inter: dislash.SlashInteraction, amount: int, target: discord.User = dislash.OptionParam(lambda i: i.author, description="the target user", )):
    await inter.reply(f"{amount=} {target=}")

bot.run(input())