<img src="https://cdn.discordapp.com/attachments/808032994668576829/813135069661102110/dislash_emb_crop.png" align="left" width="50" title="dislash.py">
<h1>dislash.py</h1>


[![Discord](https://discord.com/api/guilds/808030843078836254/embed.png)](https://discord.gg/gJDbCw8aQy)
[![PyPi](https://img.shields.io/pypi/v/dislash.py.svg)](https://pypi.org/project/dislash.py)
[![Python](https://img.shields.io/pypi/pyversions/dislash.py.svg)](https://pypi.python.org/pypi/dislash.py)

An extending library for [discord.py](https://github.com/Rapptz/discord.py) that allows to build awesome message components and slash commands.


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
* Works with discord.py <=1.7.3, >=2.0.0a



# Examples
💡 This library requires **[discord.py](https://github.com/Rapptz/discord.py)**.


## Creating a slash-command
In this example registration is automatic.
If you want to register slash-commands separately, see docs.

```python
from discord.ext import commands
from dislash import SlashClient

bot = commands.Bot(command_prefix="!")
slash = SlashClient(client)
test_guilds = [12345, 98765]

@slash.command(
    name="hello", # Defaults to function name
    description="Says hello",
    guild_ids=test_guilds # If not specified, the command is registered globally
    # Global registration takes up to 1 hour
)
async def hello(inter):
    await inter.reply("Hello!")

bot.run("BOT_TOKEN")
```


## Creating buttons

This example shows how to send a message with buttons.

```python
from discord.ext import commands
from dislash import SlashClient, ActionRow, Button, ButtonStyle

bot = commands.Bot(command_prefix="!")
slash = SlashClient(bot)

@bot.command()
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

bot.run("BOT_TOKEN")
```


## Creating menus

This example shows how to send a message with a menu.

```python
from discord.ext import commands
from dislash import SlashClient, SelectMenu, SelectOption

bot = commands.Bot(command_prefix="!")
slash = SlashClient(bot)

@bot.command()
async def test(ctx):
    msg = await ctx.send(
        "This message has a select menu!",
        components=[
            SelectMenu(
                custom_id="test",
                placeholder="Choose up to 2 options",
                max_values=2,
                options=[
                    SelectOption("Option 1", "value 1"),
                    SelectOption("Option 2", "value 2"),
                    SelectOption("Option 3", "value 3")
                ]
            )
        ]
    )
    # Wait for someone to click on it
    inter = await msg.wait_for_dropdown()
    # Send what you received
    labels = [option.label for option in inter.select_menu.selected_options]
    await inter.reply(f"Options: {', '.join(labels)}")

bot.run("BOT_TOKEN")
```


# Links
- **[Documentation](https://dislashpy.readthedocs.io/en/latest)**
- **[PyPi](https://pypi.org/project/dislash.py)**
- **[Our Discord](https://discord.gg/gJDbCw8aQy)**


# Downloads


[![Downloads](https://pepy.tech/badge/dislash.py)](https://pepy.tech/project/dislash.py)
[![Downloads](https://pepy.tech/badge/dislash.py/month)](https://pepy.tech/project/dislash.py)
![Downloads](https://pepy.tech/badge/dislash.py/week)
