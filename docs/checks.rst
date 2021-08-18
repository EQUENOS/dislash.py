.. currentmodule:: dislash


Slash command checks
====================

Introduction
------------

This section contains documentation of decorator-based checks that **dislash.py** has.

Here's a possible use case:

.. code-block:: python

    import dislash
    from discord.ext import commands

    bot = commands.Bot(command_prefix="!")
    inter_client = dislash.InteractionClient(bot)

    @inter_client.slash_command(description="A command for admins")
    @dislash.has_permissions(administrator=True)
    async def hello(inter):
        await inter.reply("Hello, administrator!")
    
    bot.run("BOT_TOKEN")

If you want to respond with something like *"You're missing permissions!"*,
you should add an error handler using ``on_slash_command_error(inter, error)`` event,
learn more about it here: :ref:`on_slash_command_error`


.. _slash_checks:

Checks
------

.. autofunction:: check

.. autofunction:: check_any

.. autofunction:: cooldown

.. autofunction:: has_role

.. autofunction:: has_any_role

.. autofunction:: has_permissions

.. autofunction:: has_guild_permissions

.. autofunction:: dm_only

.. autofunction:: guild_only

.. autofunction:: is_owner

.. autofunction:: is_nsfw

.. autofunction:: bot_has_role

.. autofunction:: bot_has_any_role

.. autofunction:: bot_has_permissions

.. autofunction:: bot_has_guild_permissions
