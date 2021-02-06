Examples
========

Registering a slash-command
---------------------------

.. seealso::

    :ref:`slash-command_constructor` and why is it important


.. code-block:: python

    import discord
    from discord.ext import commands
    from dislash import slash_commands
    # Import slash-command constructor
    from dislash.interactions import *

    # Init a client instance using discord.py
    client = commands.Bot(command_prefix="!")
    # Init a <SlashClient> instance
    slash_client = slash_commands.SlashClient(client)

    @client.event
    async def on_connect():
        # Let's register a /random command in Discord API
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

    import discord
    from random import randint
    from discord.ext import commands
    from dislash import slash_commands

    # Init a client instance using discord.py
    client = commands.Bot(command_prefix="!")
    # Init a <SlashClient> instance
    # in order to start tracking slash-command interactions
    slash_client = slash_commands.SlashClient(client)


    # Let's make a function that responds to /random
    @slash_client.command()
    async def random(interaction):
        # interaction is instance of `interactions.Interaction`
        # Read more about it in docs
        a = interaction.data.get_option('start').value
        b = interaction.data.get_option('end').value
        if b < a: a, b = b, a
        await interaction.reply(randint(a, b))
