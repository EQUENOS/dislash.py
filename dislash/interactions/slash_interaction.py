import discord
from .interaction import *


__all__ = (
    "ResponseType",
    "InteractionDataOption",
    "InteractionData",
    "Interaction",
    "SlashInteraction"
)


class Resolved:
    def __init__(self, *, payload, guild, state):
        members = payload.get("members", {})
        self.members = {}
        self.users = {}
        for ID, data in payload.get("users", {}).items():
            if ID in members:
                self.members[ID] = discord.Member(
                    data={**members[ID], "user": data},
                    guild=guild,
                    state=state
                )
            else:
                self.users[ID] = discord.User(
                    state=state,
                    data=data
                )
        self.roles = {
            ID: discord.Role(guild=guild, state=state, data=data)
            for ID, data in payload.get("roles", {}).items()
        }
        channels = payload.get('channels', {})
        self.channels = {}
        for ID, c in channels.items():
            c['position'] = 0
            factory, ch_type = discord._channel_factory(c['type'])
            if factory:
                self.channels[ID] = factory(guild=guild, data=c, state=state)

    def __repr__(self):
        return "<Resolved users={0.users} members={0.members}roles={0.roles} channels={0.channels}>".format(self)

    def get(self, any_id):
        if any_id in self.members:
            return self.members[any_id]
        if any_id in self.users:
            return self.users[any_id]
        if any_id in self.roles:
            return self.roles[any_id]
        if any_id in self.channels:
            return self.channels[any_id]


class InteractionDataOption:
    '''
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
    '''
    def __init__(self, *, data, resolved: Resolved):
        self.name = data['name']
        self.value = data.get('value')
        # Some devices may return old-formatted Interactions
        # We have to figure out the best matching type in this case
        if "type" in data:
            self.type = data["type"]
        elif isinstance(self.value, bool):
            self.type = 5
        elif isinstance(self.value, int):
            self.type = 4
        else:
            self.type = 3
        # Type 6 and higher requires resolved data
        if self.type == 6:
            if self.value in resolved.members:
                self.value = resolved.members[self.value]
            elif self.value in resolved.users:
                self.value = resolved.users[self.value]
        elif self.type == 7:
            if self.value in resolved.channels:
                self.value = resolved.channels[self.value]
        elif self.type == 8:
            if self.value in resolved.roles:
                self.value = resolved.roles[self.value]
        elif self.type == 9:
            value = resolved.get(self.value)
            if value is not None:
                self.value = value
        # I'm not sure if this is still useful
        # They've probably updated arg validation on all platforms
        if self.type > 5 and isinstance(self.value, str):
            self.value = int(self.value)
        # Converting sub options
        self.options = {
            o['name']: InteractionDataOption(data=o, resolved=resolved)
            for o in data.get('options', [])
        }
    
    def __repr__(self):
        return "<InteractionDataOption name='{0.name}' value={0.value} options={0.options}>".format(self)

    def _to_dict_values(self, connectors: dict=None):
        connectors = connectors or {}
        out = {}
        for kw, val in self.options.items():
            new_kw = connectors.get(kw, kw)
            if val.type > 2:
                out[new_kw] = val.value
            else:
                out[new_kw] = val
        return out

    @property
    def sub_command(self):
        opt = self.option_at(0)
        if opt is not None and opt.type == 1:
            return opt
    
    def get_option(self, name: str):
        '''
        Get the raw :class:`InteractionDataOption` matching the specified name

        Parameters
        ----------
        name : str
            The name of the option you want to get
        
        Returns
        -------
        option : InteractionDataOption | ``None``
        '''
        return self.options.get(name)
    
    def get(self, name: str, default=None):
        '''
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
        '''
        for n, o in self.options.items():
            if n == name:
                return o.value if o.type > 2 else o
        return default

    def option_at(self, index: int):
        """Similar to :class:`InteractionData.option_at`"""
        return list(self.options.values())[index] if 0 <= index < len(self.options) else None


class InteractionData:
    '''
    Attributes
    ----------
    id : int
    name : str
        The name of activated slash-command
    options : dict
        | Represents options of the slash-command.
        | {``name``: :class:`InteractionDataOption`, ...}
    '''
    def __init__(self, *, data, guild, state):
        resolved = Resolved(
            payload=data.get('resolved', {}),
            guild=guild,
            state=state
        )
        self.id = int(data['id'])
        self.name = data['name']
        self.options = {
            o['name']: InteractionDataOption(data=o, resolved=resolved)
            for o in data.get('options', [])
        }
    
    def __repr__(self):
        return "<InteractionData id={0.id} name='{0.name}' options={0.options}>".format(self)

    def __getitem__(self, key):
        if isinstance(key, str):
            opt = self.get_option(key)
        elif isinstance(key, int):
            opt = self.option_at(key)
        else:
            raise TypeError(f'unsupported key type. Expected str or int, but received {type(key)} instead')
        if opt is None:
            return None
        return opt.value if opt.type > 2 else opt

    def _to_dict_values(self, connectors: dict=None):
        connectors = connectors or {}
        out = {}
        for kw, val in self.options.items():
            new_kw = connectors.get(kw, kw)
            if val.type > 2:
                out[new_kw] = val.value
            else:
                out[new_kw] = val._to_dict_values(connectors)
        return out

    def _wrap_choices(self, slash_command):
        def recursive_wrapper(wrapped_data, parent):
            for option in parent.options:
                data_option = wrapped_data.get_option(option.name)
                if data_option is None:
                    continue
                if len(option._choice_connectors) > 0:
                    data_option.value = option._choice_connectors.get(
                        data_option.value,
                        data_option.value
                    )
                recursive_wrapper(data_option, option)
        recursive_wrapper(self, slash_command)

    @property
    def sub_command(self):
        opt = self.option_at(0)
        if opt is not None and opt.type == 1:
            return opt
    
    @property
    def sub_command_group(self):
        opt = self.option_at(0)
        if opt is not None and opt.type == 2:
            return opt

    def get_option(self, name: str):
        '''
        Get the raw :class:`InteractionDataOption` matching the specified name

        Parameters
        ----------
        name : str
            The name of the option you want to get
        
        Returns
        -------
        option : :class:`InteractionDataOption` | ``None``
        '''
        return self.options.get(name)
    
    def get(self, name: str, default=None):
        '''
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
        '''
        opt = self.options.get(name)
        if opt is None:
            return default
        return opt.value if opt.type > 2 else opt

    def option_at(self, index: int):
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


class SlashInteraction(BaseInteraction):
    '''
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
    '''
    def __init__(self, client, payload):
        super().__init__(client, payload)

        state = client._connection
        self.prefix = "/" # Just in case
        self.data = InteractionData(
            data=payload.get('data', {}),
            guild=self.guild,
            state=state
        )
        self.invoked_with = self.data.name
        self.slash_command = None
        self.sub_command_group = None
        self.sub_command = None

    def __repr__(self):
        return (
            "<SlashInteraction id={0.id} version={0.version} type={0.type} "
            "token='{0.token}' guild={0.guild} channel={0.channel} "
            "author={0.author} data={0.data!r}>"
        ).format(self)

    def __getitem__(self, key):
        return self.data[key]

    def _wrap_choices(self, slash_command):
        self.data._wrap_choices(slash_command)

    def get(self, name: str, default=None):
        """Equivalent to :class:`InteractionData.get`"""
        return self.data.get(name, default)
    
    def get_option(self, name: str):
        """Equivalent to :class:`InteractionData.get_option`"""
        return self.data.get_option(name)

    def option_at(self, index: int):
        """Equivalent to :class:`InteractionData.option_at`"""
        return self.data.option_at(index)


Interaction = SlashInteraction
