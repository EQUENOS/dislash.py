.. currentmodule:: dislash

.. _slash_commands_guide:

Slash commands
==============

Introduction
------------

As you've already noticed, Discord makes all slash commands look like a part of the interface.
This is possible because every slash command is registered before people can use it.
Even though this library registers your commands automatically, you should still design
every slash command yourself ;)

What are interactions?

| 1. User inputs data using special interface
| 2. Discord converts this data into valid command args
| 3. Discord API sends the data to your app

The data you receive is called :class:`SlashInteraction`.

There're 2 types of slash commands: global and local (per guild).
Global commands are visible everywhere, including bot DMs.
Per guild commands are only visible in corresponding guilds.

.. note::

    | **Global** command registration takes more than **1 hour**.
    | **Guild** command registration is **instant**.


Basic example
-------------

In this example we're using the following objects and methods:

* :class:`InteractionClient` to activate the extension
* :class:`SlashClient.command` to make a command
* :class:`SlashInteraction` represented by ``inter`` (see the code below)

.. code-block:: python

    from discord.ext import commands
    from dislash import InteractionClient

    bot = commands.Bot(command_prefix="!")
    # test_guilds param is an optional list of guild IDs
    inter_client = InteractionClient(bot, test_guilds=[12345])

    @inter_client.slash_command(description="Test command")
    async def test(inter):
        await inter.reply("Test")

    bot.run("BOT_TOKEN")



A command with arguments
------------------------

Let's make a command that shows the avatar of the user.
If user isn't specified, it shows the avatar of the author.

In addition to all previous methods, we're going to use these:

* :class:`Option` to make an option
* :class:`OptionType` to specify the option type

This is required for further command registration.

.. code-block:: python

    import discord
    from discord.ext import commands
    from dislash import InteractionClient, Option, OptionType

    bot = commands.Bot(command_prefix="!")
    inter_client = InteractionClient(bot, test_guilds=[12345])

    @inter_client.slash_command(
        description="Shows the avatar of the user",
        options=[
            Option("user", "Enter the user", OptionType.USER)
            # By default, Option is optional
            # Pass required=True to make it a required arg
        ]
    )
    async def avatar(inter, user=None):
        # If user is None, set it to inter.author
        user = user or inter.author
        # We are guaranteed to receive a discord.User object,
        # because we specified the option type as Type.USER

        emb = discord.Embed(
            title=f"{user}'s avatar",
            color=discord.Color.blue()
        )
        emb.set_image(url=user.avatar_url)
        await inter.reply(embed=emb)

    bot.run("BOT_TOKEN")



Slash subcommands
-----------------

Creating subcommands is as easy as creating commands.
The only difference is the decorator we use.

In addition to all previous methods, we're going to use :class:`CommandParent.sub_command`
(represented by ``say.sub_command`` in the code)

.. code-block:: python

    from discord.ext import commands
    from dislash import InteractionClient

    bot = commands.Bot(command_prefix="!")
    inter_client = InteractionClient(bot, test_guilds=[12345])

    @inter_client.slash_command(description="Has subcommands")
    async def say(inter):
        # This is just a parent for 2 subcommands
        # It's not necessary to do anything here,
        # but if you do, it runs for any subcommand nested below
        pass
    
    # For each subcommand you can specify individual options and other parameters,
    # see the "Objects and methods" reference to learn more.
    @say.sub_command(description="Says hello")
    async def hello(inter):
        await inter.reply("Hello!")
    
    @say.sub_command(description="Says bye")
    async def goodbye(inter):
        await inter.reply("Bye!")

    bot.run("BOT_TOKEN")


Subcommand groups
-----------------

You can make a command with groups of subcommands using
:class:`CommandParent.sub_command_group` and :class:`SubCommandGroup.sub_command`

**Partial code:**

.. code-block:: python

    @inter_client.slash_command(description="Has groups")
    async def groups(inter):
        pass
    
    @groups.sub_command_group()
    async def group_1(inter):
        pass
    
    @group_1.sub_command()
    async def blue(inter):
        # This will be displayed as
        # /groups group_1 blue
        pass
    
    @group_1.sub_command()
    async def green(inter):
        # This will be displayed as
        # /groups group_1 green
        pass
    
    @groups.sub_command_group()
    async def group_2(inter):
        # You got the idea
        pass

    bot.run("BOT_TOKEN")

