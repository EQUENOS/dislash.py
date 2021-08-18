.. currentmodule:: events

Events
======

| The library provides you with some new events related to interactions.
| Let's assume that you have this in your code:

::

    from discord.ext import commands
    from dislash import *

    bot = commands.Bot(command_prefix="!")
    slash = SlashClient(bot)

Here're 3 different ways of working with dislash events:

.. code-block:: python

    @slash.event
    async def on_event():
        # ...

.. code-block:: python

    @bot.listen()
    async def on_event():
        # ...

.. code-block:: python

    # For cogs
    @commands.Cog.listener()
    async def on_event(self):
        # ...



.. _on_ready:

on_ready
--------

.. autofunction:: on_ready



.. _on_auto_register:

on_auto_register
----------------

.. autofunction:: on_auto_register



.. _on_button_click:

on_button_click
---------------

.. autofunction:: on_button_click



.. _on_dropdown:

on_dropdown
-----------

.. autofunction:: on_dropdown



.. _on_slash_command:

on_slash_command
----------------

.. autofunction:: on_slash_command




.. _on_user_command:

on_user_command
---------------

.. autofunction:: on_user_command




.. _on_message_command:

on_message_command
------------------

.. autofunction:: on_message_command




.. _on_slash_command_error:

on_slash_command_error
----------------------

.. autofunction:: on_slash_command_error




.. _on_user_command_error:

on_user_command_error
---------------------

.. autofunction:: on_user_command_error




.. _on_message_command_error:

on_message_command_error
------------------------

.. autofunction:: on_message_command_error
