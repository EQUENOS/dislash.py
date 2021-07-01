.. currentmodule:: dislash

Objects and methods
===================

.. _slash_client:

SlashClient
-----------

.. autoclass:: SlashClient

    .. automethod:: event

    .. automethod:: command

    .. automethod:: get_global_command

    .. automethod:: get_global_command_named

    .. automethod:: get_guild_command

    .. automethod:: get_guild_command_named

    .. automethod:: get_guild_commands

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

    .. automethod:: overwrite_global_commands

    .. automethod:: overwrite_guild_commands

    .. automethod:: delete_global_commands

    .. automethod:: delete_guild_commands

    .. automethod:: fetch_global_command_named

    .. automethod:: fetch_guild_command_named

    .. automethod:: edit_global_command_named

    .. automethod:: edit_guild_command_named

    .. automethod:: delete_global_command_named

    .. automethod:: delete_guild_command_named

    .. automethod:: fetch_guild_command_permissions

    .. automethod:: batch_fetch_guild_command_permissions

    .. automethod:: edit_guild_command_permissions

    .. automethod:: batch_edit_guild_command_permissions



.. _command_parent:

CommandParent
-------------

.. autoclass:: CommandParent

    .. automethod:: sub_command

    .. automethod:: sub_command_group



.. _sub_command_group:

SubCommandGroup
---------------

.. autoclass:: SubCommandGroup

    .. automethod:: sub_command



.. _message_interaction:

MessageInteraction
------------------

.. autoclass:: MessageInteraction

    .. automethod:: fetch_initial_response

    .. automethod:: create_response

    .. automethod:: reply

    .. automethod:: edit

    .. automethod:: delete

    .. automethod:: followup



.. _slash_interaction:

SlashInteraction
----------------

.. autoclass:: SlashInteraction

    .. automethod:: get

    .. automethod:: get_option

    .. automethod:: option_at

    .. automethod:: fetch_initial_response

    .. automethod:: create_response

    .. automethod:: reply

    .. automethod:: edit

    .. automethod:: delete

    .. automethod:: followup




.. _interaction_data:

InteractionData
---------------

.. autoclass:: InteractionData

    .. automethod:: get

    .. automethod:: get_option

    .. automethod:: option_at



.. _interaction_data_option:

InteractionDataOption
---------------------

.. autoclass:: InteractionDataOption

    .. automethod:: get

    .. automethod:: get_option

    .. automethod:: option_at



.. _response_type:

ResponseType
------------

.. autoclass:: ResponseType
    


.. _button_style:

ButtonStyle
-----------

.. autoclass:: ButtonStyle



.. _button:

Button
------

.. autoclass:: Button



.. _select_menu:

SelectOption
------------

.. autoclass:: SelectOption



.. _select_menu:

SelectMenu
----------

.. autoclass:: SelectMenu



.. _action_row:

ActionRow
---------

.. autoclass:: ActionRow

    .. automethod:: enable_buttons

    .. automethod:: disable_buttons



.. _auto_rows:

auto_rows
---------

.. autofunction:: auto_rows



.. _slash_command:

SlashCommand
------------

.. autoclass:: SlashCommand



.. _option:

Option
------

.. autoclass:: Option



.. _option_choice:

OptionChoice
------------

.. autoclass:: OptionChoice



.. _option_type:

OptionType
----------

.. autoclass:: Type



.. _slash_command_permissions:

SlashCommandPermissions
-----------------------

.. autoclass:: SlashCommandPermissions

    .. automethod:: from_pairs

    .. automethod:: from_ids

    .. automethod:: from_dict

    .. automethod:: to_dict



.. _raw_command_permission:

RawCommandPermission
--------------------

.. autoclass:: RawCommandPermission

    .. automethod:: from_pair

    .. automethod:: from_dict

    .. automethod:: to_dict



.. _click_listener:

ClickListener
-------------

.. autoclass:: ClickListener

    .. automethod:: matching_condition

    .. automethod:: matching_id

    .. automethod:: from_user

    .. automethod:: not_from_user

    .. automethod:: no_checks

    .. automethod:: timeout

    .. automethod:: kill
