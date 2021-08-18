.. _examples:

Examples
========

A simple slash command
----------------------

.. code-block:: python

    from discord.ext import commands
    from dislash import InteractionClient

    bot = commands.Bot(command_prefix="!")
    inter_client = InteractionClient(bot)

    @inter_client.slash_command(description="Sends Hello")
    async def hello(interaction):
        await interaction.reply("Hello!")
    
    bot.run("BOT_TOKEN")

.. seealso::

    | What's interaction? See :ref:`slash_interaction` to learn more.


Slash embed
-----------

Let's make something more complicated than **/hello**.
For example, a command that generates an embed.

.. code-block:: python

    import discord
    from discord.ext import commands
    from dislash import InteractionClient, Option, OptionType

    bot = commands.Bot(command_prefix="!")
    inter_client = InteractionClient(bot)
    test_guilds = [12345]   # Insert ID of your guild here

    @inter_client.slash_command(
        guild_ids=test_guilds,
        description="Builds a custom embed",
        options=[
            Option('title', 'Makes the title of the embed', OptionType.STRING),
            Option('description', 'Makes the description', OptionType.STRING),
            Option('color', 'The color of the embed', OptionType.STRING)

            # Note that all args are optional
            # because we didn't specify required=True in Options
        ]
    )
    async def embed(inter, title=None, description=None, color=None):
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
        await inter.respond(embed=emb, hide_user_input=True)
    
    bot.run("BOT_TOKEN")

.. seealso::

    | :ref:`option` to learn more about slash command options.

Here's the result we've just achieved:

.. image:: https://cdn.discordapp.com/attachments/808032994668576829/814250796672745482/unknown.png





Slash user-info
---------------

It's time to work with different argument types.
This example shows how to easily make a **/user-info** command

.. code-block:: python

    import discord
    from discord.ext import commands
    from dislash import InteractionClient, Option, OptionType

    bot = commands.Bot(command_prefix="!")
    inter_client = InteractionClient(bot)
    test_guilds = [12345]

    @inter_client.slash_command(
        guild_ids=test_guilds,
        name="user-info",
        description="Shows user's profile",
        options=[
            Option("user", "Specify any user", OptionType.USER),
        ]
    )
    async def user_info(inter, user=None):
        # Default user is the command author
        user = user or inter.author

        emb = discord.Embed(color=discord.Color.blurple())
        emb.title = str(user)
        emb.description = (
            f"**Created at:** `{user.created_at}`\n"
            f"**ID:** `{user.id}`"
        )
        emb.set_thumbnail(url=user.avatar_url)
        await inter.respond(embed=emb)
    
    bot.run("BOT_TOKEN")

Here's how this slash command looks like in Discord:

.. image:: https://cdn.discordapp.com/attachments/808032994668576829/814251227789393930/unknown.png



Buttons
-------

.. code-block:: python

    from discord.ext import commands
    from dislash import InteractionClient, ActionRow, Button, ButtonStyle

    bot = commands.Bot(command_prefix="!")
    inter_client = InteractionClient(bot)

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
    
    
    
Context menus
-------------

This example shows how to create context menu commands and interact with them. 
Context menu commands are actions that can be triggered from user and message context menus.

.. code-block:: python

    from discord.ext import commands
    from dislash import InteractionClient

    bot = commands.Bot(command_prefix="!")
    inter_client = InteractionClient(bot)

    @inter_client.user_command(name="Press me")
    async def press_me(inter):
        # User commands are visible in user context menus
        # They can be global or per guild, just like slash commands
        await inter.respond(f"Hello {inter.author} and {inter.target}")

    @inter_client.message_command(name="Resend")
    async def resend(inter):
        # Message commands are visible in message context menus
        # inter is instance of ContextMenuInteraction
        await inter.respond(inter.message.content)

    bot.run("BOT_TOKEN")
