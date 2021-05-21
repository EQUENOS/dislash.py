import asyncio
import datetime
import discord
from discord.errors import InvalidArgument
from discord.http import Route
from discord.utils import DISCORD_EPOCH
from .slash_commands.slash_command import *


__all__ = (
    "ResponseType",
    "InteractionDataOption",
    "InteractionData",
    "Interaction",
    "Type",
    "OptionChoice",
    "Option",
    "SlashCommand"
)


class ResponseType:
    """
    All possible response type values. Used in :class:`Interaction.reply`

    Attributes
    ----------
    Pong = 1
    Acknowledge = 2 [DEPRECATED]
    ChannelMessage = 3 [DEPRECATED]
    ChannelMessageWithSource = 4
    AcknowledgeWithSource = 5
    """
    Pong                     = 1
    Acknowledge              = 1
    ChannelMessage           = 3
    ChannelMessageWithSource = 4
    AcknowledgeWithSource    = 5


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
        return "<Resolved users={0.users} members={0.members}\
                roles={0.roles} channels={0.channels}>".format(self)

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
        for n, o in self.options.items():
            if n == name:
                return o.value if o.type > 2 else o
        return default

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


class Interaction:
    '''
    Every interaction with slash-commands is represented by instances of this class

    Attributes
    ----------
    id : int
    version : int
    type : int
    token : str
        Interaction token
    guild : discord.Guild
        The guild where interaction was created
    channel : :class:`discord.TextChannel`
        The channel where interaction was created
    author : :class:`discord.Member` | :class:`discord.User`
        The member/user that used the slash-command.
    data : :class:`InteractionData`
        The arguments that were passed
    created_at : :class:`datetime.datetime`
        Then interaction was created
    expired : :class:`bool`:
        Whether the interaction token is still valid
    '''
    def __init__(self, client, payload: dict):
        state = client.user._state
        self.prefix = "/" # Just in case
        self.client = client
        self.id = int(payload['id'])
        self.version = payload['version']
        self.type = payload['type']
        self.token = payload['token']
        if 'guild_id' in payload:
            self.guild = self.client.get_guild(int(payload['guild_id']))
            self.author = discord.Member(
                data=payload['member'],
                guild=self.guild,
                state=state
            )
        else:
            self.guild = None
            self.author = discord.User(
                state=state,
                data=payload['user']
            )
        self.channel_id = int(payload['channel_id'])
        self._channel = None
        self.data = InteractionData(
            data=payload.get('data', {}),
            guild=self.guild,
            state=state
        )
        self.editable = False
        self._sent = False
        self._webhook = None
    
    def __repr__(self):
        return "<Interaction id={0.id} version={0.version} type={0.type} "\
                "token='{0.token}' guild={0.guild} channel_id={0.channel_id} "\
                "author={0.author} data={0.data!r}>".format(self)
    
    @property
    def channel(self):
        if self._channel is None:
            self._channel = self.client.get_channel(self.channel_id)
        return self._channel
    @property
    def member(self):
        return self.author if self.guild is not None else None
    @property
    def user(self):
        return self.author
    @property
    def webhook(self):
        if self._webhook is None:
            self._webhook = discord.Webhook(
                {"id": self.client.user.id, "type": 1, "token": self.token},
                adapter=discord.AsyncWebhookAdapter(self.client.http._HTTPClient__session)
            )
        return self._webhook
    @property
    def created_at(self):
        return datetime.datetime.fromtimestamp(((self.id >> 22) + DISCORD_EPOCH) / 1000)
    @property
    def expired(self):
        if self._sent:
            return datetime.datetime.utcnow() - self.created_at > datetime.timedelta(minutes=15)
        else:
            return datetime.datetime.utcnow() - self.created_at > datetime.timedelta(seconds=3)

    def get(self, name: str, default=None):
        """Equivalent to :class:`InteractionData.get`"""
        return self.data.get(name, default)
    
    def get_option(self, name: str):
        """Equivalent to :class:`InteractionData.get_option`"""
        return self.data.get_option(name)

    def option_at(self, index: int):
        """Equivalent to :class:`InteractionData.option_at`"""
        return self.data.option_at(index)

    async def reply(self, content=None, *,  embed=None, embeds=None,
                                            file=None, files=None,
                                            tts=False, hide_user_input=False,
                                            ephemeral=False, delete_after=None,
                                            allowed_mentions=None, type=None,
                                            fetch_response_message=True):
        '''
        Replies to the interaction.

        Parameters
        ----------
        content : str
            content of the message that you're going so send
        embed : discord.Embed
            an embed that'll be attached to the message
        embeds : List[discord.Embed]
            a list of up to 10 embeds to attach
        file : :class:`discord.File`
            if it's the first interaction reply, the file will be ignored due to API limitations.
            Everything else is the same as in :class:`discord.TextChannel.send()` method.
        files : List[:class:`discord.File`]
            same as ``file`` but for multiple files.
        hide_user_input : bool
            if set to ``True``, user's input won't be displayed
        ephemeral : bool
            if set to ``True``, your response will only be visible to the command author
        tts : bool
            whether the message is text-to-speech or not
        delete_after : float
            if specified, your reply will be deleted after ``delete_after`` seconds
        allowed_mentions : discord.AllowedMentions
            controls the mentions being processed in this message.
        type : :class:`int` | :class:`ResponseType`
            sets the response type. If it's not specified, this method sets
            it according to ``hide_user_input``, ``content`` and ``embed`` params.
        fetch_response_message : :class:`bool`
            whether to fetch and return the response message or not. Defaults to ``True``.

        Raises
        ------
        ~discord.HTTPException
            sending the response failed
        ~discord.InvalidArgument
            Both ``embed`` and ``embeds`` are specified

        Returns
        -------
        message : :class:`discord.Message` | ``None``
            The response message that has been sent or ``None`` if the message is ephemeral
        '''
        is_empty_message = content is None and embed is None
        # Which callback type is it
        if type is None:
            if is_empty_message:
                type = 1 if hide_user_input else 5
            else:
                type = 3 if hide_user_input else 4
        # Sometimes we have to use TextChannel.send() instead
        if self._sent or self.expired or type == 3:
            return await self.channel.send(
                content=content, embed=embed,
                file=file, files=files,
                tts=tts, delete_after=delete_after,
                allowed_mentions=allowed_mentions
            )
        # JSON data formation
        data = {}
        if content is not None:
            data['content'] = str(content)
        # Embed or embeds
        if embed is not None and embeds is not None:
            raise InvalidArgument("Can't pass both embed and embeds")
        
        if embed is not None:
            if not isinstance(embed, discord.Embed):
                raise InvalidArgument('embed parameter must be discord.Embed')
            data['embeds'] = [embed.to_dict()]
        
        elif embeds is not None:
            if len(embeds) > 10:
                raise InvalidArgument('embds parameter must be a list of up to 10 elements')
            elif not all(isinstance(embed, discord.Embed) for embed in embeds):
                raise InvalidArgument('embeds parameter must be a list of discord.Embed')
            data['embeds'] = [embed.to_dict() for embed in embeds]
        # Allowed mentions
        if not is_empty_message:
            state = self.client.user._state
            if allowed_mentions is not None:
                if state.allowed_mentions is not None:
                    allowed_mentions = state.allowed_mentions.merge(allowed_mentions).to_dict()
                else:
                    allowed_mentions = allowed_mentions.to_dict()
                data['allowed_mentions'] = allowed_mentions
        # Message design
        if ephemeral:
            data["flags"] = 64
        if tts:
            data["tts"] = True
        # Final JSON formation
        _json = {"type": type}
        if len(data) > 0:
            _json["data"] = data
        # HTTP-request
        await self.client.http.request(
            Route(
                'POST', '/interactions/{interaction_id}/{token}/callback',
                interaction_id=self.id, token=self.token
            ),
            json=_json
        )
        self._sent = True
        # Type-5 responses are always editable
        if type == 5:
            self.editable = True
            return None
        # Ephemeral messages aren't stored and can't be deleted or edited
        # Same for type-1 and type-2 messages
        if ephemeral or type in (1, 2):
            return None
        self.editable = True
        if delete_after is not None:
            self.client.loop.create_task(self.delete_after(delete_after))
        if fetch_response_message:
            return await self.edit()
    
    async def edit(self, content=None, *, embed=None, embeds=None, allowed_mentions=None):
        '''
        Edits your reply to the interaction.

        Parameters
        ----------
        content : str
            Content of the message that you're going so edit
        embed : discord.Embed
            An embed that'll be attached to the message
        embeds : List[discord.Embed]
            a list of up to 10 embeds to reattach
        allowed_mentions : discord.AllowedMentions
            controls the mentions being processed in this message.
        
        Returns
        -------
        message : :class:`discord.Message`
            The message that was edited
        '''
        if not self.editable:
            raise TypeError("There's nothing to edit or the message is ephemeral.")
        # Form JSON params
        data = {}
        if content is not None:
            data['content'] = str(content)
        # Embed or embeds
        if embed is not None and embeds is not None:
            raise InvalidArgument("Can't pass both embed and embeds")
        
        if embed is not None:
            if not isinstance(embed, discord.Embed):
                raise InvalidArgument('embed parameter must be discord.Embed')
            data['embeds'] = [embed.to_dict()]
        
        elif embeds is not None:
            if len(embeds) > 10:
                raise InvalidArgument('embds parameter must be a list of up to 10 elements')
            elif not all(isinstance(embed, discord.Embed) for embed in embeds):
                raise InvalidArgument('embeds parameter must be a list of discord.Embed')
            data['embeds'] = [embed.to_dict() for embed in embeds]
        # Allowed mentions
        state = self.client.user._state
        if allowed_mentions is not None:
            if state.allowed_mentions is not None:
                allowed_mentions = state.allowed_mentions.merge(allowed_mentions).to_dict()
            else:
                allowed_mentions = allowed_mentions.to_dict()
            data['allowed_mentions'] = allowed_mentions
        # HTTP-response
        r = await self.client.http.request(
            Route(
                'PATCH', '/webhooks/{app_id}/{token}/messages/@original',
                app_id=self.client.user.id, token=self.token
            ),
            json=data
        )
        return discord.Message(
            state=state,
            channel=self.channel,
            data=r
        )
    
    async def delete(self):
        '''
        Deletes your interaction response.
        '''
        if not self.editable:
            raise TypeError("There's nothing to delete. Send a reply first.")
        # patch
        await self.client.http.request(
            Route(
                'DELETE', '/webhooks/{app_id}/{token}/messages/@original',
                app_id=self.client.user.id, token=self.token
            )
        )
        self.editable = False
    
    async def delete_after(self, delay: float):
        await asyncio.sleep(delay)
        try:
            await self.delete()
        except:
            pass

    async def followup(self, content=None, *,   embed=None, embeds=None,
                                                file=None, files=None,
                                                tts=None, allowed_mentions=None):
        """
        Sends a followup message, which is basically a channel message
        referencing the original interaction response.

        Parameters are similar to :class:`discord.TextChannel.send()`
        """
        r = await self.webhook.send(
            content=content, tts=tts,
            file=file, files=files,
            embed=embed, embeds=embeds,
            allowed_mentions=allowed_mentions
        )
        return discord.Message(
            state=self.client.user._state,
            channel=self.channel,
            data=r
        )

    send = reply

    respond = reply
