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

.. topic:: Note

    | **Global** command registration takes more than **1 hour**.
    | **Guild** command registration is **instant**.

SlashCommand
------------

.. autoclass:: SlashCommand

Option
------

.. autoclass:: Option

| This class represents a command option.

| There're 3 possible use-cases for options:
| 1. Each option is an **argument**
| 2. Each option is a **sub-command**
| 3. Each option represents a **group of sub-commands**

| In order to identify the use-case, there's such argument as ``type``
| For example, here's a command with 2 integer arguments:

Slash-command response
======================
