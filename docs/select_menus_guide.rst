.. currentmodule:: dislash

.. _select_menus_guide:

Select Menus
============

Sending a menu
--------------

Let's make a simple command that sends a menu.

In this example we're using the following objects and methods:

* :class:`InteractionClient` to enable the extension
* :class:`SelectMenu` to build the menu

.. code-block:: python

    from discord.ext import commands
    from dislash import InteractionClient, SelectMenu

    bot = commands.Bot(command_prefix="!")
    InteractionClient(bot)

    @bot.command()
    async def test(ctx):
        await ctx.send(
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
    
    bot.run("BOT_TOKEN")


Responding to a menu click
--------------------------

Let's send a menu and then respond to the first click.

.. code-block:: python

    from discord.ext import commands
    from dislash import InteractionClient, SelectMenu

    bot = commands.Bot(command_prefix="!")
    InteractionClient(bot)

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
        def check(inter):
            # inter is instance of MessageInteraction
            # read more about it in "Objects and methods" section
            if inter.author == ctx.author
        # Wait for a menu click under the message you've just sent
        inter = await msg.wait_for_dropdown(check)
        # Tell which options you received
        labels = [option.label for option in inter.select_menu.selected_options]
        await inter.reply(f"Your choices: {', '.join(labels)}")

    bot.run("BOT_TOKEN")

Here we used :class:`Message.wait_for_dropdown` method to receive an interaction with the menu.
This is cool, but if you want to track menu interactions permanently, try using the ``on_dropdown`` event.

.. code-block:: python

    @bot.event
    async def on_dropdown(inter: MessageInteraction):
        # ...
