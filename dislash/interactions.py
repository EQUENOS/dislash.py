import asyncio
import datetime
import discord
from typing import List, Union
from discord.errors import InvalidArgument
from discord.http import Route
from discord.utils import DISCORD_EPOCH


#-----------------------------------+
#       Interaction wrappers        |
#-----------------------------------+
class InteractionDataOption:
    '''
    Represents user's input for a specific option

    Attributes
    ----------
    name : str
        The name of the option
    value : Any
        The value of the option
    options : list
        The list of sub options
    '''
    def __init__(self, data: dict):
        self.name = data['name']
        self.value = data.get('value')
        if isinstance(self.value, str) and len(self.value) == 18 and self.value.isdigit():
            self.value = int(self.value)
        self.options = [InteractionDataOption(o) for o in data.get('options', [])]
    
    def get_option(self, name: str):
        '''
        Parameters
        ----------

        name : str
            The name of the sub-option you want to get
        
        Returns
        -------

        option : InteractionDataOption or ``None``
        '''
        for o in self.options:
            if o.name == name:
                return o


class InteractionData:
    '''
    Attributes
    ----------
    id : int
    name : str
        The name of activated slash-command
    options : list
        The list of options of the slash-command
    '''
    def __init__(self, data: dict):
        self.id = int(data['id'])
        self.name = data['name']
        self.options = [InteractionDataOption(o) for o in data.get('options', [])]
    
    def get_option(self, name: str):
        '''
        Parameters
        ----------

        name : str
            The name of the option you want to get
        
        Returns
        -------

        option : InteractionDataOption or ``None``
        '''
        for o in self.options:
            if o.name == name:
                return o


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
    channel : discord.TextChannel
        The channel where interaction was created
    author : discord.Member
        The member that used the slash-command
    data : InteractionData
        The arguments that were passed
    created_at : datetime.datetime
        Then interaction was created
    '''
    def __init__(self, client, payload: dict):
        self.prefix = "/" # Just in case
        self.client = client
        self.id = int(payload['id'])
        self.version = payload['version']
        self.type = payload['type']
        self.token = payload['token']
        self.guild = self.client.get_guild(int(payload['guild_id']))
        self.channel_id = int(payload['channel_id'])
        self._channel = None
        self.member = discord.Member(
            data=payload['member'],
            guild=self.guild,
            state=self.client.user._state
        )
        self.data = InteractionData(payload.get('data', {}))
        self.editable = False
    @property
    def channel(self):
        if self._channel is None:
            self._channel = self.guild.get_channel(self.channel_id)
        return self._channel
    @property
    def author(self):
        return self.member
    @property
    def created_at(self):
        return datetime.datetime.fromtimestamp(((self.id >> 22) + DISCORD_EPOCH) / 1000)

    async def reply(self, content=None, *,  embed=None, embeds=None,
                                            tts=False, hide_user_input=False,
                                            ephemeral=False, delete_after=None,
                                            allowed_mentions=None):
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
        hide_user_input : bool
            if set to ``True``, user's input won't be displayed
        ephemeral : bool
            if set to ``True``, your response will only be visible to the command author
        tts : bool
            wether the msaage is text-to-speech or not
        delete_after : float
            if specified, your reply will be deleted after ``delete_after`` seconds
        allowed_mentions : discord.AllowedMentions
            controls the mentions being processed in this message. All mentions are allowed by default.

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
        # Which callback type is it
        if content is None and embed is None:
            if hide_user_input:
                _type = 1
            else:
                _type = 5
        elif hide_user_input:
            _type = 3
        else:
            _type = 4
        # Post
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
        else:
            allowed_mentions = state.allowed_mentions and state.allowed_mentions.to_dict()
        data['allowed_mentions'] = allowed_mentions
        # Message design
        if ephemeral:
            data["flags"] = 64
        if tts:
            data["tts"] = True
        # HTTP-request
        _json = {
            "type": _type,
            "data": data
        }
        await self.client.http.request(
            Route(
                'POST', '/interactions/{interaction_id}/{token}/callback',
                interaction_id=self.id, token=self.token
            ),
            json=_json
        )
        # Ephemeral messages aren't stored and can't be deleted or edited
        if not ephemeral:
            self.editable = True
            if delete_after is not None:
                self.client.loop.create_task(self.delete_after(delete_after))
            return await self.edit()
    
    async def edit(self, content=None, embed=None):
        '''
        Edits your reply to the interaction.

        Parameters
        ----------
        content : str
            Content of the message that you're going so edit
        embed : discord.Embed
            An embed that'll be attached to the message
        
        Returns
        -------
        message : :class:`discord.Message`
            The message that was edited
        '''
        if not self.editable:
            raise TypeError("There's nothing to edit. Send a reply first.")
        # patch
        data = {}
        if content is not None:
            data['content'] = str(content)
        if embed is not None:
            data['embeds'] = [embed.to_dict()]
        r = await self.client.http.request(
            Route(
                'PATCH', '/webhooks/{app_id}/{token}/messages/@original',
                app_id=self.client.user.id, token=self.token
            ),
            json=data
        )
        return discord.Message(
            state=self.client.user._state,
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

    send = reply


#-----------------------------------+
#     Slash-command registrator     |
#          OOP Interface            |
#-----------------------------------+
class Type:
    '''
    Attributes
    ----------
    SUB_COMMAND=1
    SUB_COMMAND_GROUP=2
    STRING=3
    INTEGER=4
    BOOLEAN=5
    USER=6
    CHANNEL=7
    ROLE=8
    '''
    SUB_COMMAND       = 1
    SUB_COMMAND_GROUP = 2
    STRING            = 3
    INTEGER           = 4
    BOOLEAN           = 5
    USER              = 6
    CHANNEL           = 7
    ROLE              = 8


class OptionChoice:
    '''
    Parameters
    ----------
    name : str
        the name of the option-choice (visible to users)
    value : str or int
        the value of the option-choice
    '''

    def __init__(self, name: str, value: Union[str, int]):
        self.name = name
        self.value = value

    def __eq__(self, other):
        return (
            self.name == other.name and
            self.value == other.value
        )


class Option:
    '''
    Parameters
    ----------
    name : str
        option's name
    description : str
        option's description
    type : Type
        the option type, e.g. ``Type.USER``, see :ref:`option_type`
    choices : list
        list of option choices, type :ref:`option_choice`
    '''

    def __init__(self, name: str, description: str, type: int, required: bool=False, choices: List[OptionChoice]=None, options: list=None):
        self.name = name
        self.description = description
        self.type = type
        if required:
            self.required = True
        if choices is not None:
            self.choices = choices
        if options is not None:
            if self.type == 1:
                for opt in options:
                    if opt.type < 3:
                        raise ValueError('Unexpected sub_command in a sub_command')
            elif self.type == 2:
                for opt in options:
                    if opt.type != 1:
                        raise ValueError('Expected sub_command in this sub_command_group')
            self.options = options
    
    def __eq__(self, other):
        return (
            self.name == other.name and
            self.description == other.description and
            self.type == other.type and
            getattr(self, 'required', False) == getattr(other, 'required', False) and
            getattr(self, 'choices', []) == getattr(other, 'choices', []) and
            getattr(self, 'options', []) == getattr(other, 'options', [])
        )
    
    @classmethod
    def from_dict(cls, payload: dict):
        if 'options' in payload:
            payload['options'] = [Option.from_dict(p) for p in payload['options']]
        if 'choices' in payload:
            payload['choices'] = [OptionChoice(**p) for p in payload['choices']]
        return Option(**payload)

    def add_choice(self, choice: OptionChoice):
        '''
        Adds an OptionChoice to the list of current choices

        Parameters
        ----------

        choice : OptionChoice
            the choice you're going to add
        '''
        if 'choices' not in self.__dict__:
            self.choices = [choice]
        else:
            self.choices.append(choice)
    
    def add_option(self, option):
        '''
        Adds an option to the current list of options

        Parameters
        ----------

        option : Option
            the option you're going to add
        '''
        if 'options' not in self.__dict__:
            self.options = [option]
        else:
            if self.type == 1:
                if option.type < 3:
                    raise ValueError('Sub_command (or group) can only be folded in a sub_command_group')
            elif self.type == 2:
                if option.type != 1:
                    raise ValueError('Expected sub_command in this sub_command_group')
            self.options.append(option)

    def to_dict(self):
        payload = {
            'name': self.name,
            'description': self.description,
            'type': self.type
        }
        dct = self.__dict__
        if 'required' in dct:
            payload['required'] = True
        if 'choices' in dct:
            payload['choices'] = [c.__dict__ for c in self.choices]
        if 'options' in dct:
            payload['options'] = [o.to_dict() for o in self.options]
        return payload


class SlashCommand:
    '''A base class for building slash-commands.

    Parameters
    ----------
    name : str
        The command name
    description : str
        The command description (it'll be displayed by discord)
    options : List[Option]
        The options of the command. See :ref:`option`
    '''

    def __init__(self, name: str, description: str, options: list=None, **kwargs):
        self.id = kwargs.get('id')
        self.application_id = kwargs.get('application_id')
        self.name = name
        self.description = description
        self.options = options if options is not None else []
    
    def __eq__(self, other):
        return (
            self.name == other.name and
            self.description == other.description and
            self.options == other.options
        )

    @classmethod
    def from_dict(cls, payload: dict):
        if 'options' in payload:
            payload['options'] = [Option.from_dict(p) for p in payload['options']]
        return SlashCommand(**payload)

    def add_option(self, option: Option):
        '''
        Adds an option to the current list of options

        Parameters
        ----------

        option : Option
            the option you're going to add
        '''
        self.options.append(option)

    def to_dict(self):
        res = {
            'description': self.description,
            'options': [o.to_dict() for o in self.options]
        }
        if hasattr(self, 'name'):
            res['name'] = self.name
        return res
