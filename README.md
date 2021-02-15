# dislash.py

[![Discord](https://discord.com/api/guilds/808030843078836254/embed.png)](https://discord.gg/gJDbCw8aQy)
[![PyPi](https://img.shields.io/pypi/v/dislash.py.svg)](https://pypi.org/project/dislash.py)
[![Python](https://img.shields.io/pypi/pyversions/dislash.py.svg)](https://pypi.python.org/pypi/dislash.py)

An extending library for [discord.py](https://github.com/Rapptz/discord.py) that allows to build awesome slash-commands.

⭐ Star us on GitHub - we do really need your feedback and help!



# Installation

Run any of these commands in terminal:
```
pip install dislash.py
```
```
python -m pip install dislash.py
```



# Features

* Supports automatic registration of slash-commands
* Supports manual and automatic sharding
* Convenient decorator-based interface
* OOP-based slash-command constructor



# Examples
💡 This library does require **[discord.py](https://github.com/Rapptz/discord.py)** installed.


## Creating a slash-command
In this example registration is automatic.
If you want to register slash-commands separately, see examples below.

```python
from discord.ext import commands
from dislash import slash_commands
from dislash.interactions import *

client = commands.Bot(command_prefix="!")
slash = slash_commands.SlashClient(client)
test_guilds = [12345, 98765]

@slash.command(
    name="hello", # Defaults to function name
    description="Says hello",
    guild_ids=test_guilds # If not specified, the command is registered globally
    # Global registration takes more than 1 hour
)
async def hello(inter):
    await inter.reply("Hello!")

client.run("BOT_TOKEN")
```


## Registering a slash-command

This example only shows how to register a slash-command.

```python
from discord.ext import commands
from dislash import slash_commands
from dislash.interactions import *

client = commands.Bot(command_prefix="!")
slash = slash_commands.SlashClient(client)
test_guild_ID = 12345

@slash.event
async def on_ready():
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
    await slash.register_global_slash_command(sc)
    # Discord API uploads GLOBAL commands for more than 1 hour
    # That's why I highly recommend .register_guild_slash_command for testing:
    await slash.register_guild_slash_command(test_guild_id, sc)

client.run("BOT_TOKEN")
```
You should register a slash-command only once in order to make it work. You can always edit it if you want, using `.edit_global_slash_command` / `.edit_guild_slash_command` methods.


## Responding to a slash-command

It's assumed that you've already registered the command.

```python
from random import randint
from discord.ext import commands
from dislash import slash_commands
from dislash.interactions import *

client = commands.Bot(command_prefix="!")
slash = slash_commands.SlashClient(client)

@slash.command()
async def random(interaction):
    # interaction is instance of `interactions.Interaction`
    # It's pretty much the same as "ctx" from discord.py
    # except <message> attribute is replaced by <data>
    a = interaction.data.get_option('start').value
    b = interaction.data.get_option('end').value
    if b < a: a, b = b, a
    await interaction.reply(randint(a, b))

client.run("BOT_TOKEN")
```



# Links
> **[Documentation](https://dislashpy.readthedocs.io/en/latest)**

> **[PyPi](https://pypi.org/project/dislash.py)**

> **[Our Discord](https://discord.gg/gJDbCw8aQy)**
