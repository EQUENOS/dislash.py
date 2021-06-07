.. _examples:

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
    from dislash import *

    bot = commands.Bot(command_prefix="!")
    slash = SlashClient(bot)

    # If description is specified, the command will be
    # registered automatically
    @slash.command(description="Sends Hello")
    async def hello(interaction):
        await interaction.reply("Hello!")
    
    bot.run("BOT_TOKEN")



Manual registration
-------------------

.. seealso::

    :ref:`slash-command_constructor` and why is it important

In this example we are **only** registering a command.
This is useful when you learn how to register different types of commands.

.. code-block:: python

    from discord.ext import commands
    from dislash import *

    bot = commands.Bot(command_prefix="!")
    slash = SlashClient(bot)

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
        await slash.register_global_slash_command(sc)
        # Discord API uploads global commands for more than 1 hour
        # That's why I highly recommend .register_guild_slash_command for testing:
        await slash.register_guild_slash_command(guild_id, sc)


Okay, we've just registered **/random**.
If you try to execute it, nothing happens.
That's absolutely normal, because we haven't defined a response yet.
In order to start responding to **/random**, run the following code:

.. code-block:: python

    from random import randint
    from discord.ext import commands
    from dislash import *

    bot = commands.Bot(command_prefix="!")
    slash = SlashClient(bot)

    @slash.command()
    async def random(interaction):
        a = interaction.data.get('start')
        b = interaction.data.get('end')
        if b < a: a, b = b, a
        await interaction.reply(randint(a, b))

    bot.run("BOT_TOKEN")




Slash embed
-----------

Let's make something more complicated than **/hello**.
For example, a command that generates an embed.

::

    from discord.ext import commands
    from dislash import *

    bot = commands.Bot(command_prefix="!")
    slash = SlashClient(bot)
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
        title = inter.get('title')
        desc = inter.get('description')
        color = inter.get('color')
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
    
    bot.run("BOT_TOKEN")

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
    from dislash import *

    bot = commands.Bot(command_prefix="!")
    slash = SlashClient(bot)
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
        user = ctx.get("user", ctx.author)

        emb = discord.Embed(color=discord.Color.blurple())
        emb.title = str(user)
        emb.description = (
            f"**Created at:** `{user.created_at}`\n"
            f"**ID:** `{user.id}`
        )
        emb.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=emb)
    
    bot.run("BOT_TOKEN")

Here's how this slash command looks like in Discord:

.. image:: https://cdn.discordapp.com/attachments/808032994668576829/814251227789393930/unknown.png



Buttons
-------

::

    from discord.ext import commands
    from dislash import *

    bot = commands.Bot(command_prefix="!")
    slash = SlashClient(bot)

    @bot.command()
    async def test(ctx):
        # Make a row of buttons
        row_of_buttons = ActionRow(
            Button(
                style=ButtonStyle.green,
                label="Green button",
                custom_id="green"
            ),
            Button(
                style=ButtonStyle.red,
                label="Red button",
                custom_id="red"
            )
        )
        # Send a message with buttons
        msg = await ctx.send(
            "This message has buttons!",
            components=[row_of_buttons]
        )
        # Wait for someone to click on them
        inter = await msg.wait_for_button_click(check)
        # Send what you received
        button_text = inter.clicked_button.label
        await inter.reply(f"Button: {button_text}")

    bot.run("BOT_TOKEN")
