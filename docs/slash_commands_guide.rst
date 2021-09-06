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

Alternative option syntax
=========================

Sometimes defining options as an argument of the decorator may look confusing, especially when you introduce connectors.
This can be fixed using a :ref:`fastapi-like<https://fastapi.tiangolo.com/>` paramater "descriptors" using :class:`OptionParam`.

**An example of a command using OptionParam:**

.. code-block:: python

    import discord
    from discord.ext import commands

    from dislash import InteractionClient, Option, OptionType, OptionParam, SlashInteraction

    bot = commands.Bot(command_prefix="!")
    inter_client = InteractionClient(bot, test_guilds=[12345])

    # before:
    @inter_client.slash_command(
        options=[
            Option("target", description="The target user", type=OptionType.USER, required=True),
            Option("action", description="-"),
            Option("where", description="The location", type=OptionType.CHANNEL),
        ],
        connectors={"where": "channel"}
    )
    async def complicated(
        inter: SlashInteraction, 
        target: discord.User, 
        action: str = "hug", 
        channel: discord.TextChannel = None
    ):
        if not isinstance(channel, discord.TextChannel):
            handle_error()  # remember that you could recieve channel categories
        pass


    # after:
    @inter_client.slash_command()
    async def simple(
        inter: SlashInteraction,
        target: discord.User = OptionParam(..., description="The target user"),
        action: str = "hug",
        channel: discord.TextChannel = OptionParam(None, name="where", description="The location"),
    ):
        pass

As you can see the commands syntax is shorter and keeps the option attribute definitions close to the actual parameter.

Defaults
--------

The default value should be provided as the first argument to :class:`OptionParam`. If the parameter is required you can either not provide it or set it to an ellipsis `...`

.. code-block:: python

    @inter_client.slash_command()
    async def command(
        inter: SlashInteraction,
        a: float = OptionParam(desc="Required float"),
        b: int = OptionParam(..., desc="Required int"),
        c: str = OptionParam("default", desc="Optional str")
    ):
        pass

Sometimes the default value cannot be hardcoded, such as an author or the current channel. In this case you can just pass in any callable.

.. code-block:: python

    author = lambda inter: inter.author
    
    @inter_client.slash_command()
    async def command(
        inter: SlashInteraction,
        user: discord.User = OptionParam(author),
        channel: discord.abc.TextChannel = OptionParam(lambda i: i.channel),
    ):
        pass

Converters
----------

In some cases you may require the argument to be converted to a type not supported by slash commands. Simply pass a converter callable as the `converter` argument

.. code-block:: python

    @inter_client.slash_command()
    async def command(
        inter: SlashInteraction,
        item: str = OptionParam(desc="An item that will be pluralized", converter=lambda arg: arg + 's')
    ):
        pass

Choices
-------

Choices are highly simplified using :class:`OptionParam`. Simply use either :class:`typing.Literal` or :class:`enum.Enum`.

.. code-block:: python

    # before:
    @inter_client.slash_command(
        options=[
            Option(
                "arg",
                description="An argument picked from multiple choices",
                type=OptionType.STRING,
                required=True,
                choices=[
                    OptionChoice("argument 1", "arg1"),
                    OptionChoice("argument 2", "arg2"),
                    OptionChoice("argument 3", "arg3"),
                ],
            )
        ]
    )
    async def original(inter: SlashInteraction, arg: str):
        pass

    # ------------------------------
    # using Enum:
    class Arg(str, Enum):
        # inheriting from str ensures the typing is correct
        # underscores are replaced by spaces
        argument_1 = "arg1"
        argument_2 = "arg2"
        argument_3 = "arg3"


    @inter_client.slash_command()
    async def enumerator(
        inter: SlashInteraction, 
        arg: Arg = OptionParam(desc="An argument picked from multiple choices")
    ):
        pass


    # ------------------------------
    # using one-line Enum:
    from dislash import option_enum
    # both of these options are valid:
    OneLineArg = option_enum({"argument 1": "arg1", "argument 2": "arg2", "argument 3": "arg3"})
    OneLineArg = option_enum(argument_1="arg1", argument_2="arg2", argument_3="arg3"})

    @inter_client.slash_command()
    async def oneline_enumerator(
        inter: SlashInteraction, 
        arg: OneLineArg = OptionParam(desc="An argument picked from multiple choices")
    ):
        pass


    # ------------------------------
    # using Literal:
    @inter_client.slash_command()
    async def literal(
        inter: SlashInteraction,
        arg: Literal["arg1", "arg2", "arg3"]
    ):
        # this approach assumes the values and what the user is gonna be picking from are gonna be the same
        # that's generally unlikely so you should always prefer enumerators
        pass


Supported types for slash command argument
------------------------------------------

- STRING - `str`
- INTEGER - `int`
- NUMBER - `float`
- BOOLEAN - `bool`
- USER - `discord.abc.User`, `discord.User`, `discord.Member`
- CHANNEL - `discord.abc.GuildChannel`, `discord.TextChannel`, `discord.VoiceChannel`, `discord.CategoryChannel`, `discord.StageChannel`, `discord.StoreChannel`
- ROLE - `discord.Role`
- MENTIONABLE - `discord.abc.Snowflake`, `Union[discord.Member, discord.Role]`