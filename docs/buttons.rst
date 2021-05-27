.. currentmodule:: dislash.interactions

Buttons
=======

Here's a basic example of how buttons work:

::

    from discord.ext import commands
    from dislash.interactions import *
    from dislash.slash_commands import *

    client = commands.Bot(command_prefix="!")
    slash = SlashClient(client)

    @client.command()
    async def test(ctx):
        row = ActionRow(
            Button(
                style=ButtonStyle.green,
                label="Click me!",
                custom_id="test_button"
            )
        )
        await ctx.send("I have a button!", components=[row])
        def check(inter):
            return inter.author == ctx.author
        inter = await ctx.wait_for_button_click(check=check)
        await inter.reply(f"Button: {inter.clicked_button.label}")
    
    client.run("BOT_TOKEN")

.. _action_row:

ActionRow
---------

.. autoclass:: ActionRow




.. _button:

Button
------

.. autoclass:: Button




.. _button_interaction:

ButtonInteraction
-----------------

.. autoclass:: ButtonInteraction

    .. automethod:: reply

    .. automethod:: edit

    .. automethod:: delete

    .. automethod:: followup
