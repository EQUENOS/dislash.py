import discord
from .message_components import *
from .interaction import *


__all__ = (
    "MessageInteraction",
    "ButtonInteraction"
)


class PartialTextChannel:
    def __init__(self, channel_id):
        self.id = channel_id


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
            if msg_data.get("flags") == 64:
                # The original message is ephemeral
                message_id = int(msg_data["id"])
                self.message = None
                self.components = []
                for message in client.cached_ephemeral_messages:
                    if message.id == message_id and message.channel.id == self.channel.id:
                        self.message = message
                        self.components = message.components
                        break
            else:
                components = msg_data.get("components", [])
                self.components = [ActionRow.from_dict(comp) for comp in components]
                # For some reason "channel_id" might not be included in message data
                if "channel_id" in msg_data:
                    channel = client.get_channel(int(msg_data["channel_id"]))
                else:
                    msg_data["channel_id"] = self.channel_id
                    channel = self.channel
                # For some reason "channel_id" in message reference might not be included
                if "message_reference" in msg_data:
                    if "channel_id" not in msg_data["message_reference"]:
                        msg_data["message_reference"]["channel_id"] = None if channel is None else channel.id
                # channel must not be None, because channel.id attr is needed in discord.Message.__init__
                self.message = discord.Message(
                    state=state,
                    channel=channel or PartialTextChannel(0),
                    data=msg_data
                )
        
        component_data = data.get("data", {})
        component_type = component_data.get("component_type", 1)
        custom_id = component_data.get("custom_id")
        self.component = None
        for action_row in self.components:
            for component in action_row.components:
                if component.custom_id == custom_id and component.type == component_type:
                    self.component = component
                    if component_type == ComponentType.SelectMenu:
                        self.component._select_options(component_data.get("values", []))
                    break
            if self.component is not None:
                break
    
    @property
    def clicked_button(self) -> Button:
        if self.component.type == ComponentType.Button:
            return self.component

    @property
    def button(self) -> Button:
        return self.clicked_button
    
    @property
    def select_menu(self) -> SelectMenu:
        if self.component.type == ComponentType.SelectMenu:
            return self.component


ButtonInteraction = MessageInteraction
