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




Slash hello
-----------

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




Slash embed
-----------

Let's make something more complicated than **/hello**.
For example, a command that generates an embed.

::

    from discord.ext import commands
    from dislash.interactions import *
    from dislash.slash_commands import SlashClient

    client = commands.Bot(command_prefix="!")
    slash = SlashClient(client)
    test_guilds = [12345]   # Insert ID of your guild here

    @slash.command(
        guild_ids=test_guilds,
        description="Builds a custom embed",
        options=[
            Option('title', 'Makes the title of the embed', Type.STRING),
            Option('description', 'Makes the description', Type.STRING),
            Option('color', 'The color of the embed', Type.STRING)

            # Note that all args are optional
            # because we didn't specify required=True in Options
        ]
    )
    async def embed(inter):
        # Get arguments
        title = inter.data.get('title')
        desc = inter.data.get('description')
        color = inter.data.get('color')
        # Converting color
        if color is not None:
            try:
                color = await commands.ColorConverter().convert(inter, color)
            except:
                color = None
        if color is None:
            color = discord.Color.default()
        # Generating an embed
        emb = discord.Embed(color=color)
        if title is not None:
            emb.title = title
        if desc is not None:
            emb.description = desc
        # Sending the output
        await inter.reply(embed=emb, hide_user_input=True)
    
    client.run("BOT_TOKEN")

.. seealso::

    | :ref:`interaction_data` to learn more about how arguments are passed.
    | :ref:`option` to learn more about slash-command options.

Here's the result we've just achieved:

.. image:: https://cdn.discordapp.com/attachments/808032994668576829/814250796672745482/unknown.png





Slash user-info
---------------

It's time to work with different argument types.
This example shows how to easily make a **/user-info** command

::

    from discord.ext import commands
    from dislash.interactions import *
    from dislash.slash_commands import SlashClient

    client = commands.Bot(command_prefix="!")
    slash = SlashClient(client)
    test_guilds = [12345]

    @slash.command(
        guild_ids=test_guilds,
        name="user-info",
        description="Shows user's profile",
        options=[
            Option("user", "Specify any user", Type.USER),
        ]
    )
    async def user_info(ctx):
        # Returns <ctx.author> if "user" argument wasn't passed
        user = ctx.data.get("user", ctx.author)

        emb = discord.Embed(color=discord.Color.blurple())
        emb.title = str(user)
        emb.description = (
            f"**Created at:** `{user.created_at}`\n"
            f"**ID:** `{user.id}`
        )
        emb.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=emb)
    
    client.run("BOT_TOKEN")

Here's how this slash command looks like in Discord:

.. image:: https://cdn.discordapp.com/attachments/808032994668576829/814251227789393930/unknown.png
