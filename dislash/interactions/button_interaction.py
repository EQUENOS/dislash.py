import discord
from .message_components import *
from .interaction import *


__all__ = ("ButtonInteraction",)


class ButtonInteraction(BaseInteraction):
    """
    Represents a button interaction.
    Obtainable via :class:`discord.Context.wait_for_button_click`
    and in ``on_button_click`` event.

    Attributes
    ----------
    author : :class:`discord.Member` | :class:`discord.User`
        The user that clicked the button
    channel : :class:`discord.Messageable`
        The channel where the click happened
    guild : :class:`discord.Guild` | ``None``
        The guild where the click happened
    message : :class:`discord.Message`
        The message where the button was clicked
    components : :class:`list`
        A list of :class:`ActionRow` instances containing buttons
    clicked_button : :class:`Button`
        The button that was clicked
    """
    def __init__(self, client, data):
        super().__init__(client, data)
        state = client._connection

        msg_data = data.get("message")
        if msg_data is None:
            self.message = None
            self.components = []
        else:
            components = msg_data.pop("components", [])
            self.components = [ActionRow.from_dict(comp) for comp in components]
            channel_id = int(msg_data["channel_id"])
            self.message = discord.Message(
                state=state,
                channel=client.get_channel(channel_id),
                data=msg_data
            )
        
        custom_id = data.get("data", {}).get("custom_id")
        self.clicked_button = None
        for action_row in self.components:
            for button in action_row.components:
                if button.custom_id == custom_id:
                    self.clicked_button = button
                    break
            if self.clicked_button is not None:
                break
    
    @property
    def button(self):
        return self.clicked_button
