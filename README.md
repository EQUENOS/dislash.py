<img src="https://cdn.discordapp.com/attachments/808032994668576829/813135069661102110/dislash_emb_crop.png" align="left" width="50" title="dislash.py">
<h1>dislash.py</h1>


[![Discord](https://discord.com/api/guilds/808030843078836254/embed.png)](https://discord.gg/gJDbCw8aQy)
[![PyPi](https://img.shields.io/pypi/v/dislash.py.svg)](https://pypi.org/project/dislash.py)
[![Python](https://img.shields.io/pypi/pyversions/dislash.py.svg)](https://pypi.python.org/pypi/dislash.py)

An extending library for [discord.py](https://github.com/Rapptz/discord.py) that allows to build awesome slash-commands and message components.

📄 Slash commands is a new discord API feature that allows to build user-friendly commands. Once "`/`" is pressed on keyboard, the entire list of slash-commands pops up. The list includes hints and short descriptions which make exploring your bot much easier.


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
* OOP-based slash-command and button constructor



# Examples
💡 This library requires **[discord.py](https://github.com/Rapptz/discord.py)**.


## Creating a slash-command
In this example registration is automatic.
If you want to register slash-commands separately, see docs.

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
    # Global registration takes up to 1 hour
)
async def hello(inter):
    await inter.reply("Hello!")

client.run("BOT_TOKEN")
```


## Creating buttons

This example shows how to send a message with buttons.

```python
from discord.ext import commands
from dislash.slash_commands import *
from dislash.interactions import *

client = commands.Bot(command_prefix="!")
slash = SlashClient(client)

@client.command()
async def test(ctx):
    # Make a row of buttons
    row_of_buttons = ActionRow(
        Button(
            style=ButtonStyle.green,
            label="Green button",
            custom_id="green"
        ),
        Button(
            style=ButtonStyle.red,
            label="Red button",
            custom_id="red"
        )
    )
    # Send a message with buttons
    msg = await ctx.send(
        "This message has buttons!",
        components=[row_of_buttons]
    )
    # Wait for someone to click on them
    def check(inter):
        return inter.message.id == msg.id
    inter = await ctx.wait_for_button_click(check)
    # Send what you received
    button_text = inter.clicked_button.label
    await inter.reply(f"Button: {button_text}")

client.run("BOT_TOKEN")
```



# Links
- **[Documentation](https://dislashpy.readthedocs.io/en/latest)**
- **[PyPi](https://pypi.org/project/dislash.py)**
- **[Our Discord](https://discord.gg/gJDbCw8aQy)**
