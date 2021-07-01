# This file was created for the documentation of
# event references and is not a working code sample.


from dislash import *


async def on_ready():
    """
    An event which is activated when the dislash extension is ready
    and all slash commands are synced (if there're any)
    """
    pass


async def on_slash_command_error(interaction, error):
    """
    An event which is called every time a slash command fails
    due to some error. This also includes :class:`SlashCheckFailure`

    Parameters
    ----------
    interaction : :class:`SlashInteraction`
        the interaction with slash command
    error : :class:`SlashCommandError`
        the error that was raised
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
        the interaction with the slash command
    """
    pass
