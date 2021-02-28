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




Making our first command
------------------------

Let's make a **/hello** command that will send "Hello!" to the chat.

::

    from discord.ext import commands
    from dislash.interactions import *
    from dislash.slash_commands import SlashClient

    client = commands.Bot(command_prefix="!")
    slash = SlashClient(client)
    test_guilds = [12345]   # Insert ID of your guild here

    # If description is specified, the command is auto-registered
    @slash.command(
        guild_ids=test_guilds,   # Delete this param if you want to register globally
        description="Says Hello"
    )
    async def hello(ctx):
        await ctx.send("Hello!")
    
    client.run("BOT_TOKEN")

.. note::

    | Per-guild registration is **instant**, while global registration takes up to **1 hour** to complete.
    | In order to register a command globally, do not specify the ``guild_ids`` parameter.

And here we go! We've just made a simple slash-command named **/hello**

.. image:: https://cdn.discordapp.com/attachments/808032994668576829/814250609640996864/unknown.png

.. note:: For more examples, see :ref:`examples`
