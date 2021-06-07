# Should be named message_interaction.py

import discord
from .message_components import *
from .interaction import *


__all__ = (
    "MessageInteraction",
    "ButtonInteraction"
)


class MessageInteraction(BaseInteraction):
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
        A list of :class:`ActionRow` instances containing other components
    component : :class:`Component`
        The component that author interacted with
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
        self.component = None
        for action_row in self.components:
            for component in action_row.components:
                if component.custom_id == custom_id:
                    self.component = component
                    break
            if self.component is not None:
                break
    
    @property
    def clicked_button(self):
        if self.component.type == ComponentType.Button:
            return self.component

    @property
    def button(self):
        return self.clicked_button


ButtonInteraction = MessageInteraction
