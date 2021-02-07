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

Registration
^^^^^^^^^^^^

First of all, we have to register our command in Discord. Otherwise, it'll never work (see :ref:`slash-command_constructor`)

::

    from discord.ext import commands
    from dislash.interactions import *
    from dislash.slash_commands import SlashClient

    client = commands.Bot(command_prefix="!")
    slash = SlashClient(client)
    test_guild_id = 123   # Insert ID of your guild here

    @client.event
    async def on_connect():
        sc = SlashCommand(
            name="hello",
            description="Sends Hello! to the chat"
        )
        await slash.register_guild_slash_command(test_guild_id, sc)
    
    client.run("BOT_TOKEN")

.. note::

    | We used ``.register_guild_slash_command`` here because per-guild registration is instant,
      while global commands are cached for **1 hour**.
    | However, you should use ``.register_global_slash_command`` if you want to make your command work on multiple servers.

| It's enough to run this code once.
| Now it's time to make a response for our **/hello** command.

Response
^^^^^^^^

| Tracking slash-command interactions is as easy as placing a decorator above your function.
| Let's take a look:

::

    import discord
    from discord.ext import commands
    from dislash.slash_commands import SlashClient

    client = commands.Bot(command_prefix="!")
    slash = SlashClient(client)

    @slash.command()
    async def hello(interaction):
        await interaction.reply("Hello!")
    
    client.run("BOT_TOKEN")

.. note:: Here ``interaction`` is something similar to ``ctx`` from discord.py, see :ref:`interaction` for more info.

And here we go! We've just made a simple slash-command named **/hello**




Making a slash-embed
--------------------

Registration
^^^^^^^^^^^^

.. note:: Again, we're not using global registration in order to see the result instantly.

::

    from discord.ext import commands
    from dislash.interactions import *
    from dislash.slash_commands import SlashClient

    client = commands.Bot(command_prefix="!")
    slash = SlashClient(client)
    test_guild_id = 123   # Insert ID of your guild here

    @client.event
    async def on_connect():
        sc = SlashCommand(
            name="embed",
            description="Builds a custom embed",
            options=[
                Option('title', 'Makes the title of the embed', Type.STRING),
                Option('description', 'Makes the description', Type.STRING),
                Option('color', 'The color of the embed', Type.STRING)
                # Notice that all args are optional,
                # because we didn't specify required=True in Options
            ]
        )
        await slash.register_guild_slash_command(test_guild_id, sc)
    
    client.run("BOT_TOKEN")

.. seealso:: :ref:`option` to learn more about slash-command options.

Response
^^^^^^^^

::

    import discord
    from discord.ext import commands
    from dislash.slash_commands import SlashClient

    client = commands.Bot(command_prefix="!")
    slash = SlashClient(client)

    @slash.command()
    async def embed(inter):
        # Let's get arguments
        title = inter.data.get_option('title')
        desc = inter.data.get_option('description')
        color = inter.data.get_option('color')
        # All of these might be None, because they are optional args
        # Converting color
        if color is not None:
            try:
                color = await commands.ColorConverter().convert(inter, color.value)
            except:
                color = None
        if color is None:
            color = discord.Color.default()
        # Generating an embed
        emb = discord.Embed(color=color)
        if title is not None:
            emb.title = title.value
        if desc is not None:
            emb.description = desc.value
        # Sending the output
        await inter.reply(embed=emb, hide_user_input=True)
    
    client.run("BOT_TOKEN")

.. seealso:: :ref:`interaction_data` to learn more about how arguments are passed.