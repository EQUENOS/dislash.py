.. currentmodule:: dislash


.. _quickstart:

Quickstart
==========

Installation
------------

Enter one of these commands to install the library:

::

    pip install dislash.py


::

    python -m pip install dislash.py


Or just clone the repo: https://github.com/EQUENOS/dislash.py




Authorising
-----------

| Before we start, make sure your bot has ``application.commands`` scope, in case you want to make some slash commands.
| In order to grant it, authorise (or reauthorise) your bot with this tick pressed:

.. image:: https://cdn.discordapp.com/attachments/808032994668576829/808061105855397899/scopes.png




Creating a simple command
-------------------------

Let's make a **/hello** command that will send "Hello!" to the chat.

.. code-block:: python

    from discord.ext import commands
    from dislash import InteractionClient

    bot = commands.Bot(command_prefix="!")
    # test_guilds param is optional, this is a list of guild IDs
    inter_client = InteractionClient(bot, test_guilds=[12345])

    @inter_client.slash_command(description="Says Hello")
    async def hello(ctx):
        await ctx.send("Hello!")
    
    bot.run("BOT_TOKEN")

.. note::

    | Per-guild registration is **instant**, while global registration takes up to **1 hour** to complete.
    | In order to register a command globally, do not specify the ``test_guilds`` / ``guild_ids`` parameters.

And here we go! We've just made a simple slash-command named **/hello**

.. image:: https://cdn.discordapp.com/attachments/808032994668576829/814250609640996864/unknown.png




Playing with buttons
--------------------

Let's make a text command that sends 2 buttons and removes them as soon as one of them is pressed.

.. code-block:: python

    from discord.ext import commands
    from dislash import InteractionClient, ActionRow, Button, ButtonStyle

    bot = commands.Bot(command_prefix="!")
    inter_client = InteractionClient(bot)

    @bot.command()
    async def test(ctx):
        # Create a row of buttons
        row = ActionRow(
            Button(
                style=ButtonStyle.red,
                label="Red pill",
                custom_id="red_pill"
            ),
            Button(
                style=ButtonStyle.blurple,
                label="Blue pill",
                custom_id="blue_pill"
            )
        )
        # Note that we assign a list of rows to components
        msg = await ctx.send("Choose your pill:", components=[row])
        # This is the check for button_click waiter
        def check(inter):
            return inter.author == ctx.author
        # Wait for a button click under the bot's message
        inter = await msg.wait_for_button_click(check=check)
        # Respond to the interaction
        await inter.reply(
            f"Your choice: {inter.clicked_button.label}",
            components=[] # This is how you remove buttons
        )

    bot.run("BOT_TOKEN")


.. image:: https://cdn.discordapp.com/attachments/642107341868630024/851521774016528414/unknown.png

.. note::

    :class:`InteractionClient` should always be called in the main file,
    even if you're not making any slash commands. This class modifies
    some **discord.py** methods so they work with buttons.


More examples
-------------

.. note:: For more examples, see :ref:`examples`
