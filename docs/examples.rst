Examples
========

Auto registration
-----------------

.. note::

    In this example registration is automatic.
    If you want to perform registration separately, see :ref:`slash-command_constructor`
    and exmaples below this one.

.. code-block:: python

    from discord.ext import commands
    from dislash import slash_commands
    from dislash.interactions import *

    client = commands.Bot(command_prefix="!")
    slash = slash_commands.SlashClient(client)

    # If description is specified, the command will be
    # registered automatically
    @slash.command(description="Sends Hello")
    async def hello(interaction):
        await interaction.reply("Hello!")
    
    client.run("BOT_TOKEN")



Registering a slash-command
---------------------------

.. seealso::

    :ref:`slash-command_constructor` and why is it important


.. code-block:: python

    from discord.ext import commands
    from dislash import slash_commands
    from dislash.interactions import *

    client = commands.Bot(command_prefix="!")
    slash = slash_commands.SlashClient(client)

    @slash.event
    async def on_ready():
        sc = SlashCommand(
            name="random",
            description="Returns a random number from the given range",
            options=[
                Option(
                    name="start",
                    description="Enter a number",
                    type=Type.INTEGER,
                    required=True
                ),
                Option(
                    name="end",
                    description="Enter a number",
                    type=Type.INTEGER,
                    required=True
                )
            ]
        )
        # Post this command via API
        await slash_client.register_global_slash_command(sc)
        # Discord API uploads global commands for more than 1 hour
        # That's why I highly recommend .register_guild_slash_command for testing:
        await slash_client.register_guild_slash_command(guild_id, sc)



Responding to a slash-command
-----------------------------

.. code-block:: python

    from random import randint
    from discord.ext import commands
    from dislash import slash_commands

    client = commands.Bot(command_prefix="!")
    slash = slash_commands.SlashClient(client)

    @slash.command()
    async def random(interaction):
        a = interaction.data.get('start')
        b = interaction.data.get('end')
        if b < a: a, b = b, a
        await interaction.reply(randint(a, b))

    client.run("BOT_TOKEN")