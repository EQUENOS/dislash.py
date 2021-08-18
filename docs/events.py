# This file was created for the documentation of
# event references and is not a working code sample.


from dislash import *


async def on_ready():
    """
    An event which is activated when the dislash extension is ready
    and all slash commands are synced (if there're any)
    """
    pass


async def on_auto_register(global_commands_patched, patched_guilds):
    """
    An event which is called after auto synchronisation of commands.

    Parameters
    ----------
    global_commands_patched : :class:`bool`
        whether the global application commands were updated
    patched_guilds : :class:`List[int]`
        the list of IDs of guilds where the commands were updated
    """
    pass


async def on_button_click(interaction):
    """
    An event which is called on any button click of your application.

    Parameters
    ----------
    interaction : :class:`MessageInteraction`
        the interaction with the button
    """
    pass


async def on_dropdown(interaction):
    """
    An event which is called on any menu click of your application.

    Parameters
    ----------
    interaction : :class:`MessageInteraction`
        the interaction with the select menu
    """
    pass


async def on_slash_command(interaction):
    """
    An event which is called every time a slash
    command of your application is invoked.

    Parameters
    ----------
    interaction : :class:`SlashInteraction`
        the interaction with a slash command
    """
    pass


async def on_user_command(interaction):
    """
    An event which is called every time a user
    command of your application is invoked.

    Parameters
    ----------
    interaction : :class:`ContextMenuInteraction`
        the interaction with a user command
    """
    pass


async def on_message_command(interaction):
    """
    An event which is called every time a message
    command of your application is invoked.

    Parameters
    ----------
    interaction : :class:`ContextMenuInteraction`
        the interaction with a message command
    """
    pass


async def on_slash_command_error(interaction, error):
    """
    An event which is called every time a slash command fails
    due to some error. This also includes :class:`InteractionCheckFailure`

    Parameters
    ----------
    interaction : :class:`SlashInteraction`
        the interaction with a slash command
    error : :class:`ApplicationCommandError`
        the error that was raised
    """
    pass


async def on_user_command_error(interaction, error):
    """
    An event which is called every time a user command fails
    due to some error. This also includes :class:`InteractionCheckFailure`

    Parameters
    ----------
    interaction : :class:`ContextMenuInteraction`
        the interaction with a user command
    error : :class:`ApplicationCommandError`
        the error that was raised
    """
    pass


async def on_message_command_error(interaction, error):
    """
    An event which is called every time a message command fails
    due to some error. This also includes :class:`InteractionCheckFailure`

    Parameters
    ----------
    interaction : :class:`ContextMenuInteraction`
        the interaction with a message command
    error : :class:`ApplicationCommandError`
        the error that was raised
    """
    pass
