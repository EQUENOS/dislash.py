from __future__ import annotations

from typing import Any, Dict, Optional, Union

import discord

from .interaction import *
from .types import OptionType

__all__ = (
    "InteractionDataOption",
    "ApplicationCommandInteractionData",
    "SlashInteractionData",
    "ContextMenuInteractionData",
    "SlashInteraction",
    "ContextMenuInteraction",
    "Interaction",
)


class Resolved:
    def __init__(self, *, data, guild, state):
        self.members: Dict[int, discord.Member] = {}
        self.users: Dict[int, discord.User] = {}
        self.roles: Dict[int, discord.Role] = {}
        self.channels: Dict[int, discord.abc.GuildChannel] = {}
        self.messages: Dict[int, discord.Message] = {}

        users = data.get("users", {})
        members = data.get("members", {})
        roles = data.get("roles", {})
        channels = data.get("channels", {})
        messages = data.get("messages", {})

        for ID, data in users.items():
            user_id = int(ID)
            if ID in members:
                self.members[user_id] = discord.Member(
                    data={**members[ID], "user": data}, guild=guild, state=state  # type: ignore
                )
            else:
                self.users[user_id] = discord.User(state=state, data=data)

        for ID, data in roles.items():
            self.roles[int(ID)] = discord.Role(guild=guild, state=state, data=data)

        for ID, data in channels.items():
            data["position"] = 0
            factory, ch_type = discord.channel._channel_factory(data["type"])
            if factory:
                self.channels[int(ID)] = factory(guild=guild, data=data, state=state)

        for ID, data in messages.items():
            channel_id = int(data["channel_id"])
            channel = guild.get_channel(channel_id) if guild else None
            if channel is None:
                channel = state.get_channel(channel_id)
            self.messages[int(ID)] = discord.Message(state=state, channel=channel, data=data)

    def __repr__(self):
        return (
            "<Resolved users={0.users!r} members={0.members!r} "
            "roles={0.roles!r} channels={0.channels!r} "
            "messages={0.messages!r}>"
        ).format(self)

    def get(self, any_id: Any) -> Optional[discord.abc.Snowflake]:
        any_id = int(any_id)
        if any_id in self.members:
            return self.members[any_id]
        if any_id in self.users:
            return self.users[any_id]
        if any_id in self.roles:
            return self.roles[any_id]
        if any_id in self.channels:
            return self.channels[any_id]
        if any_id in self.messages:
            return self.messages[any_id]
        
        return None


class ApplicationCommandInteractionData:
    def __init__(self, *, data, guild, state):
        self.id = int(data["id"])
        self.type: int = data["type"]
        self.name: str = data["name"]
        self.resolved = Resolved(data=data.get("resolved", {}), guild=guild, state=state)


class InteractionDataOption:
    """
    Represents user's input for a specific option

    Attributes
    ----------
    name : str
        The name of the option
    value : Any
        The value of the option
    options : dict
        | Represents options of a sub-slash-command.
        | {``name``: :class:`InteractionDataOption`, ...}
    """

    def __init__(self, *, data, resolved: Resolved):
        self.name: str = data["name"]
        self.type: int = data["type"]
        self.value: Any = data.get("value")
        # Type 6 and higher requires resolved data
        if self.type == OptionType.USER:
            self.value = int(self.value)
            if self.value in resolved.members:
                self.value = resolved.members[self.value]
            elif self.value in resolved.users:
                self.value = resolved.users[self.value]
        elif self.type == OptionType.CHANNEL:
            self.value = int(self.value)
            if self.value in resolved.channels:
                self.value = resolved.channels[self.value]
        elif self.type == OptionType.ROLE:
            self.value = int(self.value)
            if self.value in resolved.roles:
                self.value = resolved.roles[self.value]
        elif self.type == OptionType.MENTIONABLE:
            self.value = int(self.value)
            self.value = resolved.get(self.value, self.value)
        # Converting sub options
        self.options: Dict[str, InteractionDataOption] = {
            o["name"]: InteractionDataOption(data=o, resolved=resolved) for o in data.get("options", [])
        }

    def __repr__(self):
        return "<InteractionDataOption name='{0.name}' value={0.value} options={0.options}>".format(self)

    def _to_dict_values(self, connectors: Dict[str, str] = None) -> Dict[str, Any]:
        connectors = connectors or {}
        out = {}
        for kw, val in self.options.items():
            new_kw = connectors.get(kw, kw)
            out[new_kw] = val.value if val.type > 2 else val
        return out

    @property
    def sub_command(self) -> Optional[InteractionDataOption]:
        opt = self.option_at(0)
        if opt is not None and opt.type == 1:
            return opt
        
        return None

    def get_option(self, name: str) -> Optional[InteractionDataOption]:
        """
        Get the raw :class:`InteractionDataOption` matching the specified name

        Parameters
        ----------
        name : str
            The name of the option you want to get

        Returns
        -------
        option : InteractionDataOption | ``None``
        """
        return self.options.get(name)

    def get(self, name: str, default: Any = None) -> Union[InteractionDataOption, Any]:  # put T here maybe
        """
        Get the value of an option with the specified name

        Parameters
        ----------
        name : str
            the name of the option you want to get
        default : any
            what to return in case nothing was found

        Returns
        -------
        option_value : any
            The option type isn't ``SUB_COMMAND_GROUP`` or ``SUB_COMMAND``
        option: InteractionDataOption | ``default``
            Otherwise
        """
        for n, o in self.options.items():
            if n == name:
                return o.value if o.type > 2 else o
        return default

    def option_at(self, index: int) -> Optional[InteractionDataOption]:
        """Similar to :class:`InteractionData.option_at`"""
        return list(self.options.values())[index] if 0 <= index < len(self.options) else None


class SlashInteractionData(ApplicationCommandInteractionData):
    """
    Attributes
    ----------
    id : :class:`int`
        The id of the interaction
    name : :class:`str`
        The name of activated slash-command
    options : :class:`dict`
        | Represents options of the slash-command.
        | {``name``: :class:`InteractionDataOption`, ...}
    resolved : :class:`Resolved`
        The collection of related objects, such as users, members, roles, channels and messages
    """

    def __init__(self, *, data, guild, state):
        super().__init__(data=data, guild=guild, state=state)
        self.options = {
            o["name"]: InteractionDataOption(data=o, resolved=self.resolved) for o in data.get("options", [])
        }

    def __repr__(self) -> str:
        return "<SlashInteractionData id={0.id} type={0.type} name={0.name!r} options={0.options!r}>".format(self)

    def __getitem__(self, key: str) -> Optional[InteractionDataOption]:
        if isinstance(key, str):
            opt = self.get_option(key)
        elif isinstance(key, int):
            opt = self.option_at(key)
        else:
            raise TypeError(f"unsupported key type. Expected str or int, but received {type(key)} instead")
        if opt is None:
            return None
        return opt.value if opt.type > 2 else opt

    def _to_dict_values(self, connectors: Dict[str, str] = None) -> Dict[str, Any]:
        connectors = connectors or {}
        out = {}
        for kw, val in self.options.items():
            new_kw = connectors.get(kw, kw)
            out[new_kw] = val.value if val.type > 2 else val._to_dict_values(connectors)
        return out

    def _wrap_choices(self, slash_command):
        def recursive_wrapper(wrapped_data, parent):
            for option in parent.options:
                data_option = wrapped_data.get_option(option.name)
                if data_option is None:
                    continue
                if len(option._choice_connectors) > 0:
                    data_option.value = option._choice_connectors.get(data_option.value, data_option.value)
                recursive_wrapper(data_option, option)

        recursive_wrapper(self, slash_command)

    @property
    def sub_command(self) -> Optional[InteractionDataOption]:
        opt = self.option_at(0)
        if opt is not None and opt.type == 1:
            return opt

    @property
    def sub_command_group(self) -> Optional[InteractionDataOption]:
        opt = self.option_at(0)
        if opt is not None and opt.type == 2:
            return opt

    def get_option(self, name: str) -> Optional[InteractionDataOption]:
        """
        Get the raw :class:`InteractionDataOption` matching the specified name

        Parameters
        ----------
        name : str
            The name of the option you want to get

        Returns
        -------
        option : :class:`InteractionDataOption` | ``None``
        """
        return self.options.get(name)

    def get(self, name: str, default: Any = None) -> Union[InteractionDataOption, Any]:
        """
        Get the value of an option with the specified name

        Parameters
        ----------
        name : str
            the name of the option you want to get
        default : any
            what to return in case nothing was found

        Returns
        -------
        option_value : any
            The option type isn't ``SUB_COMMAND_GROUP`` or ``SUB_COMMAND``
        option: :class:`InteractionDataOption` | ``default``
            Otherwise
        """
        opt = self.options.get(name)
        if opt is None:
            return default
        return opt.value if opt.type > 2 else opt

    def option_at(self, index: int) -> Optional[InteractionDataOption]:
        """
        Get an option by it's index

        Parameters
        ----------
        index : int
            the index of the option you want to get

        Returns
        -------
        option : :class:`InteractionDataOption` | ``None``
            the option located at the specified index
        """
        return list(self.options.values())[index] if 0 <= index < len(self.options) else None


class ContextMenuInteractionData(ApplicationCommandInteractionData):
    def __init__(self, data, guild, state):
        super().__init__(data=data, guild=guild, state=state)
        self.target_id = int(data["target_id"])
        self.target = self.resolved.get(self.target_id)

    def __repr__(self):
        return (
            f"<ContextMenuInteractionData id={self.id} type={self.type} " f"name={self.name!r} target={self.target!r}>"
        )

    @property
    def member(self):
        if isinstance(self.target, discord.Member):
            return self.target

    @property
    def user(self):
        if isinstance(self.target, discord.abc.User):
            return self.target

    @property
    def message(self):
        if isinstance(self.target, discord.Message):
            return self.target


class SlashInteraction(BaseInteraction):
    """
    Every interaction with slash-commands is represented by instances of this class

    Attributes
    ----------
    author : :class:`discord.Member` | :class:`discord.User`
        The member/user that used the slash-command.
    guild : discord.Guild
        The guild where interaction was created
    channel : :class:`discord.TextChannel`
        The channel where interaction was created
    data : :class:`InteractionData`
        The arguments that were passed
    created_at : :class:`datetime.datetime`
        Then interaction was created
    expired : :class:`bool`:
        Whether the interaction token is still valid
    """

    def __init__(self, client, payload):
        super().__init__(client, payload)

        state = client._connection
        self.prefix: str = "/"  # Just in case
        self.data = SlashInteractionData(data=payload.get("data", {}), guild=self.guild, state=state)
        self.invoked_with = self.data.name
        # what's this???
        self.slash_command: Optional[Any] = None
        self.sub_command_group: Optional[Any] = None
        self.sub_command: Optional[Any] = None

    def __repr__(self) -> str:
        return (
            "<SlashInteraction id={0.id} version={0.version} type={0.type} "
            "token='{0.token}' guild={0.guild} channel={0.channel} "
            "author={0.author} data={0.data!r}>"
        ).format(self)

    def __getitem__(self, key):
        return self.data[key]

    def _wrap_choices(self, slash_command):
        self.data._wrap_choices(slash_command)

    def get(self, name: str, default: Any = None):
        """Equivalent to :class:`InteractionData.get`"""
        return self.data.get(name, default)

    def get_option(self, name: str):
        """Equivalent to :class:`InteractionData.get_option`"""
        return self.data.get_option(name)

    def option_at(self, index: int):
        """Equivalent to :class:`InteractionData.option_at`"""
        return self.data.option_at(index)


class ContextMenuInteraction(BaseInteraction):
    def __init__(self, client, payload):
        super().__init__(client, payload)
        self.data = ContextMenuInteractionData(data=payload.get("data", {}), guild=self.guild, state=client._connection)
        self.user_command: Optional[Any] = None
        self.message_command: Optional[Any] = None

    def __repr__(self):
        return (
            f"<ContextMenuInteraction id={self.id} guild={self.guild!r} "
            f"channel={self.channel!r} author={self.author!r} data={self.data!r}>"
        )

    @property
    def target(self):
        return self.data.target

    @property
    def user(self):
        return self.data.user

    @property
    def member(self):
        return self.data.member

    @property
    def message(self):
        return self.data.message


Interaction = SlashInteraction
