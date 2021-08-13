.. currentmodule:: dislash

.. _context_menus_guide:

Context Menus
=============

Introduction
------------

There're 2 types of context menus:

* User commands
* Message commands

If you right click on a user and hover over the "Apps" section you'll see the list of user commands.
If there's no section named "Apps", it means that there're no user commands yet.

In order to find the list of message commands do the same actions with a message. Hover over the "Apps"
section and that's  it.

Context menu in Discord API is actually a sub section of application commands, just like slash commands.
This is why creating a context menu is really similar to creating a slash command.


Making a user command
---------------------

In this example we're using the following objects and methods:

* :class:`InteractionClient` to enable the extension
* :class:`ContextMenuInteraction` for a typehint

.. code-block:: python

    from discord.ext import commands
    from dislash import InteractionClient, ContextMenuInteraction

    bot = commands.Bot(command_prefix="!")
    inter_client = InteractionClient(bot, test_guilds=[12345])
    # test_guilds is a list of guilds for testing your application commands.
    # The list of app commands will only be visible there.
    # In order to make the commands globally visible, don't specify the test_guilds.

    @inter_client.user_command(name="Created at")
    async def created_at(inter: ContextMenuInteraction):
        # User commands always have only this ^ argument
        await inter.respond(
            f"{inter.user} was created at {inter.user.created_at}",
            ephemeral=True # Make the message visible only to the author
        )
    
    bot.run("BOT_TOKEN")


Making a message command
------------------------

In this example we're using the same objects and methods.

.. code-block:: python

    from discord.ext import commands
    from dislash import InteractionClient, ContextMenuInteraction

    bot = commands.Bot(command_prefix="!")
    inter_client = InteractionClient(bot, test_guilds=[12345])
    # test_guilds is a list of guilds for testing your application commands.
    # The list of app commands will only be visible there.
    # In order to make the commands globally visible, don't specify the test_guilds.

    @inter_client.message_command(name="Reverse")
    async def reverse(inter: ContextMenuInteraction):
        # Message commands always have only this ^ argument
        if inter.message.content:
            # Here we will send a reversed message to the chat
            await inter.respond(inter.message.content[::-1])
        else:
            # Here we will explain that the message isn't valid
            await inter.respond("There's no content", ephemeral=True)
    
    bot.run("BOT_TOKEN")


Handling errors
---------------

You can make local and global error handlers, which are similar to discord.py error handlers.

**Example of a global error handler:**

.. code-block:: python

    from discord.ext import commands
    from dislash import InteractionClient, ContextMenuInteraction

    bot = commands.Bot(command_prefix="!")
    inter_client = InteractionClient(bot, test_guilds=[12345])

    @inter_client.user_command(name="Created at")
    async def created_at(inter: ContextMenuInteraction):
        await inter.respond(
            f"{inter.user} was created at {inter.user.created_at}",
            ephemeral=True
        )
    
    @bot.event
    async def on_user_command_error(inter: ContextMenuInteraction, error):
        # This is a global error handler for user commands.
        await inter.respond(f"Failed to execute {inter.user_command.name} due to {error}")
    
    bot.run("BOT_TOKEN")

**Example of a local error handler:**

.. code-block:: python

    from discord.ext import commands
    from dislash import InteractionClient, ContextMenuInteraction

    bot = commands.Bot(command_prefix="!")
    inter_client = InteractionClient(bot, test_guilds=[12345])

    @inter_client.message_command(name="Reverse")
    async def reverse(inter: ContextMenuInteraction):
        await inter.respond(inter.message.content[::-1])
    
    @reverse.error
    async def on_reverse_error(inter: ContextMenuInteraction, error):
        # This is a local error handler specifically for "reverse" command
        await inter.respond("This message is invalid", ephemeral=True)
    
    bot.run("BOT_TOKEN")


Adding checks and cooldowns
---------------------------

You can add some checks to an application command similarly to usual commands from discord.py.
All checks from the :ref:`slash_checks` section work for any kind of application commands.

.. code-block:: python

    from discord.ext import commands
    from dislash import InteractionClient, ContextMenuInteraction, application_commands

    bot = commands.Bot(command_prefix="!")
    inter_client = InteractionClient(bot, test_guilds=[12345])

    # Here we set the command cooldown as 5 seconds per command per user
    @application_commands.cooldown(1, 5, application_commands.BucketType.user)
    @inter_client.message_command(name="Reverse")
    async def reverse(inter: ContextMenuInteraction):
        await inter.respond(inter.message.content[::-1])
    
    @bot.event
    async def on_message_command_error(inter: ContextMenuInteraction, error):
        if isinstance(error, application_commands.CommandOnCooldown):
            await inter.respond(f"Try again in {error.retry_after:.1f} s", ephemeral=True)
    
    bot.run("BOT_TOKEN")


Relevant events
---------------

.. code-block:: python

    @bot.event
    async def on_user_command(inter: ContextMenuInteraction):
        # Toggles if someone interacts with a user command of your app
        ...

.. code-block:: python

    @bot.event
    async def on_message_command(inter: ContextMenuInteraction):
        # Toggles if someone interacts with a message command of your app
        ...
