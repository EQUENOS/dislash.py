# dislash.py
It's a small extending library for [discord.py](https://github.com/Rapptz/discord.py), that allows to register slash-commands and respond to relevant interactions with them.

# Links
> **[Documentation](https://dislashpy.readthedocs.io/en/latest)**

> **[Our Discord](https://discord.gg/gJDbCw8aQy)**

# Installation
Run any of these commands in terminal to install the lib:
```
pip install dislash.py
```
```
python3 -m pip install dislash.py
```
# Examples
Note, that this library does require **[discord.py](https://github.com/Rapptz/discord.py)** installed.

## Registering a slash-command
```python
import discord
from discord.ext import commands
from dislash import slash_commands
# Import slash-command constructor
from dislash.interactions import *

# Init a client instance using discord.py
client = commands.Bot(
    command_prefix="!",
    intents=discord.Intents.default()
)
# Init a <SlashClient> instance
slash_client = slash_commands.SlashClient(client)

@client.event
async def on_connect():
    # Let's register a /random command
    sc = SlashCommand(
        name="random",
        description="Returns a random number from the given range",
        options=[
            Option(
                name="start",
                description="Enter a number",
                required=True,
                type=Type.INTEGER
            ),
            Option(
                name="end",
                description="Enter a number",
                required=True,
                type=Type.INTEGER
            )
        ]
    )
    # Post this command via API
    await slash_client.register_global_slash_command(sc)
    # Discord API uploads global commands for more than 1 hour
    # That's why I highly recommend .register_guild_slash_command for testing:
    await slash_client.register_guild_slash_command(guild_id, sc)
```
You should register a slash-command only once in order to make it work. You can always edit it if you want, using `.edit_global_slash_command` / `.edit_guild_slash_command` methods.

## Responding to a slash-command
```python
import discord
from random import randint
from discord.ext import commands
from dislash import slash_commands
# Import slash-command constructor
from dislash.interactions import *

# Init a client instance using discord.py
client = commands.Bot(
    command_prefix="!",
    intents=discord.Intents.default()
)
# Init a <SlashClient> instance
# in order to start tracking slash-command interactions
slash_client = slash_commands.SlashClient(client)


# Let's make a function that responds to /random
@slash_client.command()
async def random(interaction):
    # interaction is instance of `interactions.Interaction`
    # It's pretty much the same as "ctx" from discord.py
    # You can read more about it in docs
    a = interaction.data.get_option('start').value
    b = interaction.data.get_option('end').value
    if b < a: a, b = b, a
    await interaction.reply(randint(a, b))
```