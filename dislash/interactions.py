import datetime
import discord
from typing import List, Union
from discord.http import Route


discord_epoch = 1420070400000
#-----------------------------------+
#       Interaction wrappers        |
#-----------------------------------+
class InteractionDataOption:
    def __init__(self, data: dict):
        self.name = data['name']
        self.value = data.get('value')
        self.options = [InteractionDataOption(o) for o in data.get('options', [])]
    
    def get_option(self, name: str):
        for o in self.options:
            if o.name == name:
                return o
        return InteractionDataOption({'name': name, 'value': None})


class InteractionData:
    def __init__(self, data: dict):
        self.id = int(data['id'])
        self.name = data['name']
        self.options = [InteractionDataOption(o) for o in data.get('options', [])]
    
    def get_option(self, name: str):
        for o in self.options:
            if o.name == name:
                return o
        return InteractionDataOption({'name': name, 'value': None})


class Interaction:
    def __init__(self, client, payload: dict):
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
        return datetime.datetime.fromtimestamp(((self.id >> 22) + discord_epoch) / 1000)

    async def reply(self, content: str=None, embed: discord.Embed=None, hide_user_input=False):
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
        if embed is not None:
            data['embeds'] = [embed.to_dict()]
        json = {
            "type": _type,
            "data": data
        }
        await self.client.http.request(
            Route(
                'POST', '/interactions/{interaction_id}/{token}/callback',
                interaction_id=self.id, token=self.token
            ),
            json=json
        )


#-----------------------------------+
#     Slash-command registrator     |
#          OOP Interface            |
#-----------------------------------+
class Type:
    '''
    Attributes
    ----------

    SUB_COMMAND
    SUB_COMMAND_GROUP
    STRING
    INTEGER
    BOOLEAN
    USER
    CHANNEL
    ROLE
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
        '''
        `name` - choice name (`str`)

        `value` - choice value (`str` | `int`)
        '''
        self.name = name
        self.value = value


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
    @classmethod
    def from_dict(cls, payload: dict):
        if 'options' in payload:
            payload['options'] = [Option.from_dict(p) for p in payload['options']]
        if 'choices' in payload:
            payload['choices'] = [OptionChoice(**p) for p in payload['choices']]
        return Option(**payload)

    def add_choice(self, choice: OptionChoice):
        if 'choices' not in self.__dict__:
            self.choices = [choice]
        else:
            self.choices.append(choice)
    
    def add_option(self, option):
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

    def __init__(self, name: str, description: str, options: list=[], **kwargs):
        '''
        # Slash-command constructor

        `name` - slash-command name

        `description` - slash-command description

        `options` - slash-command options

        ## Example of registering a slash-command
        ```
        sc = SlashCommand(
            name='user-info',
            description='Shows user profile',
            options=[
                Option('user', 'Enter a user to inspect', type=6)
            ]
        )
        await slash_client.register_global_slash_command(sc)
        # slash_client is a <SlashClient> instance
        # Also check out <Option> and <OptionChoice>
        ```
        '''
        self.id = kwargs.get('id')
        self.application_id = kwargs.get('application_id')
        self.name = name
        self.description = description
        self.options = options
    @classmethod
    def from_dict(cls, payload: dict):
        if 'options' in payload:
            payload['options'] = [Option.from_dict(p) for p in payload['options']]
        return SlashCommand(**payload)

    def add_option(self, option: Option):
        self.options.append(option)

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'options': [o.to_dict() for o in self.options]
        }

