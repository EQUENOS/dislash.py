.. currentmodule:: dislash

Objects and methods
===================


ActionRow
---------

.. autoclass:: ActionRow

    .. automethod:: add_button

    .. automethod:: add_menu

    .. automethod:: disable_buttons

    .. automethod:: enable_buttons

    .. automethod:: from_dict

    .. automethod:: to_dict


ApplicationCommand
------------------

.. autoclass:: ApplicationCommand


ApplicationCommandError
-----------------------

.. autoclass:: ApplicationCommandError


ApplicationCommandInteractionData
---------------------------------

.. autoclass:: ApplicationCommandInteractionData


ApplicationCommandType
----------------------

.. autoclass:: ApplicationCommandType


BadArgument
-----------

.. autoclass:: BadArgument


BaseInteraction
---------------

.. autoclass:: BaseInteraction

    .. automethod:: create_response

    .. automethod:: delete

    .. automethod:: delete_after

    .. automethod:: edit

    .. automethod:: fetch_initial_response

    .. automethod:: followup

    .. automethod:: reply

    .. automethod:: respond

    .. automethod:: send


BotMissingAnyRole
-----------------

.. autoclass:: BotMissingAnyRole


BotMissingPermissions
---------------------

.. autoclass:: BotMissingPermissions


BotMissingRole
--------------

.. autoclass:: BotMissingRole


BucketType
----------

.. autoclass:: BucketType

    .. automethod:: try_value


Button
------

.. autoclass:: Button

    .. automethod:: from_dict

    .. automethod:: to_dict


MessageInteraction
------------------

.. autoclass:: MessageInteraction

    .. automethod:: create_response

    .. automethod:: delete

    .. automethod:: delete_after

    .. automethod:: edit

    .. automethod:: fetch_initial_response

    .. automethod:: followup

    .. automethod:: reply

    .. automethod:: respond

    .. automethod:: send


ButtonStyle
-----------

.. autoclass:: ButtonStyle


CheckAnyFailure
---------------

.. autoclass:: CheckAnyFailure


ClickListener
-------------

.. autoclass:: ClickListener

    .. automethod:: from_user

    .. automethod:: kill

    .. automethod:: matching_condition

    .. automethod:: matching_id

    .. automethod:: no_checks

    .. automethod:: not_from_user

    .. automethod:: timeout


CommandOnCooldown
-----------------

.. autoclass:: CommandOnCooldown


CommandParent
-------------

.. autoclass:: CommandParent

    .. automethod:: error

    .. automethod:: get_cooldown_retry_after

    .. automethod:: invoke

    .. automethod:: invoke_children

    .. automethod:: is_on_cooldown

    .. automethod:: reset_cooldown

    .. automethod:: sub_command

    .. automethod:: sub_command_group


Component
---------

.. autoclass:: Component


ComponentType
-------------

.. autoclass:: ComponentType


ContextMenuInteraction
----------------------

.. autoclass:: ContextMenuInteraction

    .. automethod:: create_response

    .. automethod:: delete

    .. automethod:: delete_after

    .. automethod:: edit

    .. automethod:: fetch_initial_response

    .. automethod:: followup

    .. automethod:: reply

    .. automethod:: respond

    .. automethod:: send


ContextMenuInteractionData
--------------------------

.. autoclass:: ContextMenuInteractionData


DiscordException
----------------

.. autoclass:: DiscordException


SlashInteraction
----------------

.. autoclass:: SlashInteraction

    .. automethod:: create_response

    .. automethod:: delete

    .. automethod:: delete_after

    .. automethod:: edit

    .. automethod:: fetch_initial_response

    .. automethod:: followup

    .. automethod:: get

    .. automethod:: get_option

    .. automethod:: option_at

    .. automethod:: reply

    .. automethod:: respond

    .. automethod:: send


InteractionCheckFailure
-----------------------

.. autoclass:: InteractionCheckFailure


InteractionClient
-----------------

.. autoclass:: InteractionClient

    .. automethod:: batch_edit_guild_command_permissions

    .. automethod:: batch_fetch_guild_command_permissions

    .. automethod:: command

    .. automethod:: delete_global_command

    .. automethod:: delete_global_command_named

    .. automethod:: delete_global_commands

    .. automethod:: delete_guild_command

    .. automethod:: delete_guild_command_named

    .. automethod:: delete_guild_commands

    .. automethod:: dispatch

    .. automethod:: edit_global_command

    .. automethod:: edit_global_command_named

    .. automethod:: edit_guild_command

    .. automethod:: edit_guild_command_named

    .. automethod:: edit_guild_command_permissions

    .. automethod:: event

    .. automethod:: fetch_global_command

    .. automethod:: fetch_global_command_named

    .. automethod:: fetch_global_commands

    .. automethod:: fetch_guild_command

    .. automethod:: fetch_guild_command_named

    .. automethod:: fetch_guild_command_permissions

    .. automethod:: fetch_guild_commands

    .. automethod:: get_global_command

    .. automethod:: get_global_command_named

    .. automethod:: get_guild_command

    .. automethod:: get_guild_command_named

    .. automethod:: get_guild_commands

    .. automethod:: message_command

    .. automethod:: multiple_wait_for

    .. automethod:: overwrite_global_commands

    .. automethod:: overwrite_guild_commands

    .. automethod:: register_global_command

    .. automethod:: register_guild_command

    .. automethod:: slash_command

    .. automethod:: teardown

    .. automethod:: user_command

    .. automethod:: wait_for_button_click

    .. automethod:: wait_for_dropdown


InteractionDataOption
---------------------

.. autoclass:: InteractionDataOption

    .. automethod:: get

    .. automethod:: get_option

    .. automethod:: option_at


InteractionType
---------------

.. autoclass:: InteractionType


InvokableApplicationCommand
---------------------------

.. autoclass:: InvokableApplicationCommand

    .. automethod:: error

    .. automethod:: get_cooldown_retry_after

    .. automethod:: is_on_cooldown

    .. automethod:: reset_cooldown


InvokableContextMenuCommand
---------------------------

.. autoclass:: InvokableContextMenuCommand

    .. automethod:: error

    .. automethod:: get_cooldown_retry_after

    .. automethod:: invoke

    .. automethod:: is_on_cooldown

    .. automethod:: reset_cooldown


InvokableMessageCommand
-----------------------

.. autoclass:: InvokableMessageCommand

    .. automethod:: error

    .. automethod:: get_cooldown_retry_after

    .. automethod:: invoke

    .. automethod:: is_on_cooldown

    .. automethod:: reset_cooldown


InvokableUserCommand
--------------------

.. autoclass:: InvokableUserCommand

    .. automethod:: error

    .. automethod:: get_cooldown_retry_after

    .. automethod:: invoke

    .. automethod:: is_on_cooldown

    .. automethod:: reset_cooldown


SelectOption
------------

.. autoclass:: SelectOption

    .. automethod:: from_dict

    .. automethod:: to_dict


MessageCommand
--------------

.. autoclass:: MessageCommand

    .. automethod:: from_dict

    .. automethod:: to_dict


MissingAnyRole
--------------

.. autoclass:: MissingAnyRole


MissingPermissions
------------------

.. autoclass:: MissingPermissions


MissingRole
-----------

.. autoclass:: MissingRole


NSFWChannelRequired
-------------------

.. autoclass:: NSFWChannelRequired


NoPrivateMessage
----------------

.. autoclass:: NoPrivateMessage


NotGuildOwner
-------------

.. autoclass:: NotGuildOwner


NotOwner
--------

.. autoclass:: NotOwner


Option
------

.. autoclass:: Option

    .. automethod:: add_choice

    .. automethod:: add_option

    .. automethod:: from_dict

    .. automethod:: to_dict


OptionChoice
------------

.. autoclass:: OptionChoice


OptionType
----------

.. autoclass:: OptionType


PrivateMessageOnly
------------------

.. autoclass:: PrivateMessageOnly


RawCommandPermission
--------------------

.. autoclass:: RawCommandPermission

    .. automethod:: from_dict

    .. automethod:: from_pair

    .. automethod:: to_dict


ResponseType
------------

.. autoclass:: ResponseType


SelectMenu
----------

.. autoclass:: SelectMenu

    .. automethod:: add_option

    .. automethod:: from_dict

    .. automethod:: to_dict


SlashCommand
------------

.. autoclass:: SlashCommand

    .. automethod:: add_option

    .. automethod:: from_dict

    .. automethod:: to_dict


SlashCommandPermissions
-----------------------

.. autoclass:: SlashCommandPermissions

    .. automethod:: from_dict

    .. automethod:: from_ids

    .. automethod:: from_pairs

    .. automethod:: to_dict


SlashInteractionData
--------------------

.. autoclass:: SlashInteractionData

    .. automethod:: get

    .. automethod:: get_option

    .. automethod:: option_at


SubCommand
----------

.. autoclass:: SubCommand

    .. automethod:: error

    .. automethod:: get_cooldown_retry_after

    .. automethod:: is_on_cooldown

    .. automethod:: reset_cooldown


SubCommandGroup
---------------

.. autoclass:: SubCommandGroup

    .. automethod:: error

    .. automethod:: get_cooldown_retry_after

    .. automethod:: is_on_cooldown

    .. automethod:: reset_cooldown

    .. automethod:: sub_command


UserCommand
-----------

.. autoclass:: UserCommand

    .. automethod:: from_dict

    .. automethod:: to_dict