# will remove in production
from discord.ext.commands import converter
import dislash
import discord
from discord.ext import commands

bot = commands.Bot("!")
client = dislash.InteractionClient(bot, test_guilds=[570841314200125460])


@bot.event
async def on_ready():
    print("ready")


@client.slash_command("give")
async def command(
    inter: dislash.SlashInteraction,
    amount: int = 1,
    target: discord.Member = dislash.OptionParam(
        lambda i: i.author,
        description="the target user",
    ),
    item: str = dislash.OptionParam("dollar", description="the item to give", converter=lambda inter, arg: arg + 's'),
    channel: discord.TextChannel = dislash.OptionParam(
        lambda i: i.channel, name="the-target-channel", description="name says it all"
    ),
):
    await inter.reply(f"{inter.author.mention} gave {target.mention} {amount} {item} in {channel.mention}")


print(command.registerable.options, command.connectors)

bot.run(input())