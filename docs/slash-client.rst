.. currentmodule:: dislash.slash_commands

SlashClient and Checks
======================

.. _slash_client:

SlashClient
-----------

.. autoclass:: SlashClient

    .. automethod:: event

    .. automethod:: command

    .. automethod:: fetch_global_commands

    .. automethod:: fetch_guild_commands

    .. automethod:: fetch_global_command

    .. automethod:: fetch_guild_command

    .. automethod:: register_global_slash_command

    .. automethod:: register_guild_slash_command

    .. automethod:: edit_global_slash_command

    .. automethod:: edit_guild_slash_command

    .. automethod:: delete_global_slash_command

    .. automethod:: delete_guild_slash_command




.. _slash_checks:

Checks
------

.. autofunction:: check

.. autofunction:: has_permissions

.. autofunction:: has_guild_permissions

.. autofunction:: is_guild_owner

.. autofunction:: is_owner

.. autofunction:: cooldown
