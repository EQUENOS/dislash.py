.. currentmodule:: dislash.interactions
.. _slash-command_constructor:

Slash-command constructor
=========================

This tool allows to build slash-commands for further registration.
Registering a new command is **required** due to the way Discord parses slash-commands.

| 1. User inputs data
| 2. Discord converts this data into command args
| 3. Discord API sends converted data to your app

The second step is never completed if your command isn't registered.
There're 2 types of slash-commands: global and local (per guild).

.. note::

    | **Global** command registration takes more than **1 hour**.
    | **Guild** command registration is **instant**.




.. _raw_slash_command:

SlashCommand
------------

.. autoclass:: SlashCommand

    .. automethod:: add_option

Now let's register a simple slash-command on our test server:

.. code-block:: python

    from discord.ext import commands
    from dislash.interactions import *
    from dislash.slash_commands import SlashClient

    client = commands.Bot(command_prefix="!")
    slash = SlashClient(client)
    test_guild_id = 123 # Insert your server ID here

    @slash.event
    async def on_ready():
        sc = SlashCommand(
            name="hello",
            description="Says hello"
        )
        await slash.register_guild_slash_command(test_guild_id, sc)
    
    client.run("BOT_TOKEN")

.. warning:: It's enough to register a slash command once.

.. note::

    | Registering a command isn't enough to make it work.
    | Even though it's displayed on your test server, it just eats the input and nothing happens.
    | You have to define a respose, see :ref:`interaction` and :ref:`examples`


.. _option:

Option
------

.. autoclass:: Option

    .. automethod:: add_option
    .. automethod:: add_choice

| This class represents a command option.

| There're 3 possible use-cases for options:
| 1. Each option is an **argument**
| 2. Each option is a **sub-command**
| 3. Each option represents a **group of sub-commands**

| In order to identify the use-case, there's such argument as ``type``
| For example, here's a command with 2 integer arguments:

.. code-block:: python

    sc = SlashCommand(
        name="sum",
        description="Adds 2 numbers",
        options=[
            Option("A", "Enter A", type=Type.INTEGER, required=True),
            Option("B", "Enter B", type=Type.INTEGER, required=True)
        ]
    )

| As you can see here, each ``Option`` represents a required integer argument.
| In order to register this command, paste it to the code shown in :ref:`raw_slash_command` section.

| Now, let's make something a bit more complicated.
| For exmaple, **/rename**.
| I want to define 2 sub commands: **user** and **role**.
| **/rename user** requires ``user`` and ``new-name``,
| **/rename role** requires ``role`` and ``new-name``

How does it look like in command constructor?

.. code-block:: python

    sc = SlashCommand(
        name="rename",
        description="Renames a user/role",
        options=[
            Option(
                name="user",
                description="Renames a user",
                type=Type.SUB_COMMAND,
                options=[
                    Option("user", "Specify the user", Type.USER, required=True),
                    # required=True means it's not an optional arg
                    Option("new-name", "Enter the new name", Type.STRING, True)
                ]
            ),
            Option(
                name="role",
                description="Renames a role",
                type=Type.SUB_COMMAND,
                options=[
                    Option("role", "Specify the role", Type.ROLE, True),
                    Option("new-name", "Enter the new name", Type.STRING, True)
                ]
            )
        ]
    )

In order to register this command, paste it to the code shown in :ref:`raw_slash_command` section.

So here top-level options represent sub-commands, while second-level options are just arguments for each sub command.

.. note::

    | Options of type ``Type.SUB_COMMAND_GROUP`` **must** contain options of type ``Type.SUB_COMMAND``
    | Options of type ``Type.SUB_COMMAND`` **can't** contain options of type ``Type.SUB_COMMAND`` or ``Type.SUB_COMMAND_GROUP``
    | Other options **can't** contain any sub options
    | Here ``Type`` is :ref:`option_type`




.. _option_choice:

OptionChoice
------------

.. autoclass:: OptionChoice

| How is this useful?
| Let's make a simple command named **/blep**
| I want it to let us choose one of 3 animals: dog, cat or penguin.

::

    sc = SlashCommand(
        name="blep",
        description="Sends a picture of an animal",
        options=[
            Option(
                "animal", "Choose the animal",
                type=Type.STRING, required=True,
                choices=[
                    OptionChoice("Cat", "cat"),
                    OptionChoice("Dog", "dog"),
                    OptionChoice("Penguin", "penguin")
                ]
            )
        ]
    )

So in this case users won't have to manually type which animal they'd like to see,
but choose the right option instead.



.. _option_type:

Option Type
-----------

.. autoclass:: Type
