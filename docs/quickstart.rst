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


If these commands don't work, just clone the repo: https://github.com/EQUENOS/dislash.py




Authorising
-----------

| Before we start, make sure your bot has ``application.commands`` scope.
| In order to grant it, authorise (or reauthorise) your bot with this tick pressed:

.. image:: https://cdn.discordapp.com/attachments/808032994668576829/808061105855397899/scopes.png




Creating a simple command
-------------------------

Let's make a **/hello** command that will send "Hello!" to the chat.

::

    from discord.ext import commands
    from dislash import *

    bot = commands.Bot(command_prefix="!")
    slash = SlashClient(bot)
    test_guilds = [12345]   # Insert ID of your guild here

    # If description is specified, the command is auto-registered
    @slash.command(
        guild_ids=test_guilds,   # Delete this param if you want to register globally
        description="Says Hello"
    )
    async def hello(ctx):
        await ctx.send("Hello!")
    
    bot.run("BOT_TOKEN")

.. note::

    | Per-guild registration is **instant**, while global registration takes up to **1 hour** to complete.
    | In order to register a command globally, do not specify the ``guild_ids`` parameter.

And here we go! We've just made a simple slash-command named **/hello**

.. image:: https://cdn.discordapp.com/attachments/808032994668576829/814250609640996864/unknown.png




Playing with buttons
--------------------

Let's make a text command that sends 2 buttons and removes them as soon as one of them is pressed.

::

    from discord.ext import commands
    from dislash import *

    bot = commands.Bot(command_prefix="!")
    SlashClient(bot)

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



More examples
-------------

.. note:: For more examples, see :ref:`examples`
