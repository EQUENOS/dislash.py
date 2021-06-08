.. currentmodule:: dislash.slash_commands


Button click manager
====================

This tool is one of many ways to process button clicks.
You're not forced to use it, people often prefer :class:`discord.Message.wait_for_button_click`.

.. _click_manager_tutorial:

How to use
----------

| Let's make a simple command that waits for button clicks and deletes the button on timeout.
| Introducing the ``@matching_id()`` decorator.

::

    from discord.ext import commands
    from dislash import *

    bot = commands.Bot(command_prefix="!")
    SlashClient(bot)

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


Let's say we don't want any other person except for the command author to click the buttons.
It's time to work with ``@matching_condition()`` decorator.

::

    from discord.ext import commands
    from dislash import *

    bot = commands.Bot(command_prefix="!")
    SlashClient(bot)

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

        def is_not_author(inter):
            # Note that this check must take only 1 arg
            return inter.author != ctx.author

        @on_click.matching_condition(is_not_author, cancel_others=True)
        async def on_wrong_user(inter):
            # Reply with a hidden message
            await inter.reply("You're not the author", ephemeral=True)

        @on_click.matching_id("test_button")
        async def on_test_button(inter):
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


For now, our click manager restarts the 60s timer if any listener is toggled.
Even if a stranger clicks the button. In order to prevent this, set the
``reset_timeout`` paramter to ``False``:

**Partial code:**

::

    @on_click.matching_condition(is_not_author, cancel_others=True, reset_timeout=False)
    async def on_wrong_user(inter):
        # Reply with a hidden message
        await inter.reply("You're not the author", ephemeral=True)



.. _click_listener:

ClickListener
-------------

.. autoclass:: ClickListener

    .. automethod:: matching_condition

    .. automethod:: matching_id

    .. automethod:: timeout

    .. automethod:: kill
