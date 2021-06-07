.. currentmodule:: dislash.interactions

Buttons
=======

Here's a basic example of how buttons work:

::

    from discord.ext import commands
    from dislash import *

    bot = commands.Bot(command_prefix="!")
    slash = SlashClient(bot)

    @bot.command()
    async def test(ctx):
        row = ActionRow(
            Button(
                style=ButtonStyle.green,
                label="Click me!",
                custom_id="test_button"
            )
        )
        msg = await ctx.send("I have a button!", components=[row])
        def check(inter):
            return inter.author == ctx.author
        inter = await msg.wait_for_button_click(check=check)
        await inter.reply(f"Button: {inter.clicked_button.label}")
    
    bot.run("BOT_TOKEN")

.. _action_row:

ActionRow
---------

.. autoclass:: ActionRow




.. _button:

Button
------

.. autoclass:: Button




.. _message_interaction:

MessageInteraction
-----------------

.. autoclass:: MessageInteraction

    .. automethod:: reply

    .. automethod:: edit

    .. automethod:: delete

    .. automethod:: followup



.. _auto_rows:

auto_rows
---------

.. autofunction:: auto_rows
