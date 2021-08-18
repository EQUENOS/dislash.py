.. currentmodule:: dislash

.. _buttons_guide:

Buttons
=======

Basic example
-------------

Let's make a simple command that waits for button clicks and deletes the button on timeout.

In this example we're using the following objects and methods:

* :class:`InteractionClient` to enable the extension
* :class:`ActionRow` to make a row of buttons
* :class:`Button` to design the buttons
* :class:`ClickListener` to process the button clicks
* * :class:`ClickListener.matching_id`
* * :class:`ClickListener.timeout`

.. code-block:: python

    from discord.ext import commands
    from dislash import InteractionClient, ActionRow, Button, ButtonStyle

    bot = commands.Bot(command_prefix="!")
    inter_client = InteractionClient(bot)

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
        
        # Here timeout=60 means that the listener will
        # finish working after 60 seconds of inactivity
        on_click = msg.create_click_listener(timeout=60)

        @on_click.matching_id("test_button")
        async def on_test_button(inter):
            await inter.reply("You've clicked the button!")
        
        @on_click.timeout
        async def on_timeout():
            await msg.edit(components=[])
    
    bot.run("BOT_TOKEN")

.. note::
    
    All decorated functions, except for the timeout function, must take **only one** argument,
    which is guaranteed to be an instance of :ref:`message_interaction`.



Adding layers
-------------

Let's say we don't want any other person except for the command author to click the buttons.
It's time to work with :class:`ClickListener.not_from_user` decorator.

.. code-block:: python

    from discord.ext import commands
    from dislash import InteractionClient, ActionRow, Button, ButtonStyle

    bot = commands.Bot(command_prefix="!")
    inter_client = InteractionClient(bot)

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
        
        # Here timeout=60 means that the listener will
        # finish working after 60 seconds of inactivity
        on_click = msg.create_click_listener(timeout=60)

        @on_click.not_from_user(ctx.author, cancel_others=True, reset_timeout=False)
        async def on_wrong_user(inter):
            # This function is called in case a button was clicked not by the author
            # cancel_others=True prevents all on_click-functions under this function from working
            # regardless of their checks
            # reset_timeout=False makes the timer keep going after this function is called
            await inter.reply("You're not the author", ephemeral=True)

        @on_click.matching_id("test_button")
        async def on_test_button(inter):
            # This function only works if the author presses the button
            # Becase otherwise the previous decorator cancels this one
            await inter.reply("You've clicked the button!")
        
        @on_click.timeout
        async def on_timeout():
            await msg.edit(components=[])
    
    bot.run("BOT_TOKEN")

.. note::
    
    The check must take **only one** argument, which is
    guaranteed to be an instance of :ref:`message_interaction`.
    It also must return a ``boolean`` value.

The bot is now respoding to all strangers with a hidden message and
prevents them from clicking the buttons. Note that we specified
``cancel_others=True``. This means that the click manager won't
toggle other ``@on_click...`` listeners if the author-check was activated.

What's more, the click manager doesn't reset the timeout if a stranger clicks the button.
In other words, even if the command author is no longer pressing the buttons,
other users won't prevent the click listener from exceeding the timeout.
We achieved this by setting the ``reset_timeout`` paramter to ``False``.
