.. currentmodule:: dislash

Objects and methods
===================


.. _action_row:

ActionRow
---------

.. autoclass:: ActionRow

    .. automethod:: add_button

    .. automethod:: add_menu

    .. automethod:: disable_buttons

    .. automethod:: enable_buttons

    .. automethod:: from_dict

    .. automethod:: to_dict


.. _application_command:

ApplicationCommand
------------------

.. autoclass:: ApplicationCommand


.. _application_command_error:

ApplicationCommandError
-----------------------

.. autoclass:: ApplicationCommandError


.. _application_command_interaction_data:

ApplicationCommandInteractionData
---------------------------------

.. autoclass:: ApplicationCommandInteractionData


.. _application_command_permissions:

ApplicationCommandPermissions
-----------------------------

.. autoclass:: ApplicationCommandPermissions

    .. automethod:: from_dict

    .. automethod:: from_ids

    .. automethod:: from_pairs

    .. automethod:: to_dict


.. _application_command_type:

ApplicationCommandType
----------------------

.. autoclass:: ApplicationCommandType


.. _bad_argument:

BadArgument
-----------

.. autoclass:: BadArgument


.. _base_interaction:

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


.. _bot_missing_any_role:

BotMissingAnyRole
-----------------

.. autoclass:: BotMissingAnyRole


.. _bot_missing_permissions:

BotMissingPermissions
---------------------

.. autoclass:: BotMissingPermissions


.. _bot_missing_role:

BotMissingRole
--------------

.. autoclass:: BotMissingRole


.. _bucket_type:

BucketType
----------

.. autoclass:: BucketType

    .. automethod:: try_value


.. _button:

Button
------

.. autoclass:: Button

    .. automethod:: from_dict

    .. automethod:: to_dict


.. _message_interaction:

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


.. _button_style:

ButtonStyle
-----------

.. autoclass:: ButtonStyle


.. _check_any_failure:

CheckAnyFailure
---------------

.. autoclass:: CheckAnyFailure


.. _click_listener:

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


.. _command_on_cooldown:

CommandOnCooldown
-----------------

.. autoclass:: CommandOnCooldown


.. _command_parent:

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


.. _component:

Component
---------

.. autoclass:: Component


.. _component_type:

ComponentType
-------------

.. autoclass:: ComponentType


.. _context_menu_interaction:

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


.. _context_menu_interaction_data:

ContextMenuInteractionData
--------------------------

.. autoclass:: ContextMenuInteractionData


.. _discord_exception:

DiscordException
----------------

.. autoclass:: DiscordException


.. _slash_interaction:

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


.. _interaction_check_failure:

InteractionCheckFailure
-----------------------

.. autoclass:: InteractionCheckFailure


.. _interaction_client:

InteractionClient
-----------------

.. autoclass:: InteractionClient

    .. automethod:: batch_edit_guild_command_permissions

    .. automethod:: batch_fetch_guild_command_permissions

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


.. _interaction_data_option:

InteractionDataOption
---------------------

.. autoclass:: InteractionDataOption

    .. automethod:: get

    .. automethod:: get_option

    .. automethod:: option_at


.. _interaction_type:

InteractionType
---------------

.. autoclass:: InteractionType


.. _invokable_application_command:

InvokableApplicationCommand
---------------------------

.. autoclass:: InvokableApplicationCommand

    .. automethod:: error

    .. automethod:: get_cooldown_retry_after

    .. automethod:: is_on_cooldown

    .. automethod:: reset_cooldown


.. _invokable_context_menu_command:

InvokableContextMenuCommand
---------------------------

.. autoclass:: InvokableContextMenuCommand

    .. automethod:: error

    .. automethod:: get_cooldown_retry_after

    .. automethod:: invoke

    .. automethod:: is_on_cooldown

    .. automethod:: reset_cooldown


.. _invokable_message_command:

InvokableMessageCommand
-----------------------

.. autoclass:: InvokableMessageCommand

    .. automethod:: error

    .. automethod:: get_cooldown_retry_after

    .. automethod:: invoke

    .. automethod:: is_on_cooldown

    .. automethod:: reset_cooldown


.. _invokable_user_command:

InvokableUserCommand
--------------------

.. autoclass:: InvokableUserCommand

    .. automethod:: error

    .. automethod:: get_cooldown_retry_after

    .. automethod:: invoke

    .. automethod:: is_on_cooldown

    .. automethod:: reset_cooldown


.. _select_option:

SelectOption
------------

.. autoclass:: SelectOption

    .. automethod:: from_dict

    .. automethod:: to_dict


.. _message_command:

MessageCommand
--------------

.. autoclass:: MessageCommand

    .. automethod:: from_dict

    .. automethod:: to_dict


.. _missing_any_role:

MissingAnyRole
--------------

.. autoclass:: MissingAnyRole


.. _missing_permissions:

MissingPermissions
------------------

.. autoclass:: MissingPermissions


.. _missing_role:

MissingRole
-----------

.. autoclass:: MissingRole


.. _n_s_f_w_channel_required:

NSFWChannelRequired
-------------------

.. autoclass:: NSFWChannelRequired


.. _no_private_message:

NoPrivateMessage
----------------

.. autoclass:: NoPrivateMessage


.. _not_guild_owner:

NotGuildOwner
-------------

.. autoclass:: NotGuildOwner


.. _not_owner:

NotOwner
--------

.. autoclass:: NotOwner


.. _option:

Option
------

.. autoclass:: Option

    .. automethod:: add_choice

    .. automethod:: add_option

    .. automethod:: from_dict

    .. automethod:: to_dict


.. _option_choice:

OptionChoice
------------

.. autoclass:: OptionChoice


.. _option_type:

OptionType
----------

.. autoclass:: OptionType


.. _private_message_only:

PrivateMessageOnly
------------------

.. autoclass:: PrivateMessageOnly


.. _raw_command_permission:

RawCommandPermission
--------------------

.. autoclass:: RawCommandPermission

    .. automethod:: from_dict

    .. automethod:: from_pair

    .. automethod:: to_dict


.. _response_type:

ResponseType
------------

.. autoclass:: ResponseType


.. _select_menu:

SelectMenu
----------

.. autoclass:: SelectMenu

    .. automethod:: add_option

    .. automethod:: from_dict

    .. automethod:: to_dict


.. _slash_command:

SlashCommand
------------

.. autoclass:: SlashCommand

    .. automethod:: add_option

    .. automethod:: from_dict

    .. automethod:: to_dict


.. _slash_interaction_data:

SlashInteractionData
--------------------

.. autoclass:: SlashInteractionData

    .. automethod:: get

    .. automethod:: get_option

    .. automethod:: option_at


.. _sub_command:

SubCommand
----------

.. autoclass:: SubCommand

    .. automethod:: error

    .. automethod:: get_cooldown_retry_after

    .. automethod:: is_on_cooldown

    .. automethod:: reset_cooldown


.. _sub_command_group:

SubCommandGroup
---------------

.. autoclass:: SubCommandGroup

    .. automethod:: error

    .. automethod:: get_cooldown_retry_after

    .. automethod:: is_on_cooldown

    .. automethod:: reset_cooldown

    .. automethod:: sub_command


.. _user_command:

UserCommand
-----------

.. autoclass:: UserCommand

    .. automethod:: from_dict

    .. automethod:: to_dict