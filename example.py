from enum import Enum, EnumMeta
from typing import Literal
import discord
from discord.ext import commands

from dislash import InteractionClient, Option, OptionParam, SlashInteraction
from dislash.interactions.application_command import OptionChoice, OptionType

bot = commands.Bot(command_prefix="!")
inter_client = InteractionClient(bot, test_guilds=[570841314200125460])

# before:
@inter_client.slash_command(
    options=[
        Option(
            "arg",
            description="An argument picked from multiple choices",
            type=OptionType.STRING,
            required=True,
            choices=[
                OptionChoice("argument 1", "arg1"),
                OptionChoice("argument 2", "arg2"),
                OptionChoice("argument 3", "arg3"),
            ],
        )
    ]
)
async def original(inter: SlashInteraction, arg: str):
    pass


# using Enum:
class Arg(str, Enum):
    # inheriting from str ensures the typing is correct
    # underscores are replaced by spaces
    argument_1 = "arg1"
    argument_2 = "arg2"
    argument_3 = "arg3"


@inter_client.slash_command()
async def enumerator(
    inter: SlashInteraction, arg: Arg = OptionParam(description="An argument picked from multiple choices")
):
    pass


# using one-line Enum
OneLineArg = Enum("OneLineArg", {"argument 1": "arg1", "argument 2": "arg2", "argument 3": "arg3"}, type=str)
# type=str declares the dict value type, this must be provided so typing is correct

@inter_client.slash_command()
async def oneline_enumerator(
    inter: SlashInteraction, arg: OneLineArg = OptionParam(description="An argument picked from multiple choices")
):
    pass


# using Literal:
@inter_client.slash_command()
async def literal(
    inter: SlashInteraction,
    arg: Literal["arg1", "arg2", "arg3"] = OptionParam(description="An argument picked from multiple choices"),
):
    # this approach assumes the values and what the user is gonna be picking from are gonna be the same
    # that's generally unlikely so you should always prefer enumerators
    pass


print(original.registerable.options)
print(enumerator.registerable.options)
print(oneline_enumerator.registerable.options)
print(literal.registerable.options)

bot.run(input())
