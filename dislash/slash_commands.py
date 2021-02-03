from typing import List, Union
import discord
from discord.ext import tasks
from discord.http import Route
import asyncio


#-----------------------------------+
#            Exceptions             |
#-----------------------------------+
class NotSlashCommand(discord.DiscordException):
    pass


class BadOption(discord.DiscordException):
    pass


class SlashCommandError(discord.DiscordException):
    pass


class NotGuildOwner(SlashCommandError):
    pass


class MissingPermissions(SlashCommandError):
    def __init__(self, perms):
        self.perms = perms


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
class OptionChoice:
    def __init__(self, name: str, value: Union[str, int]):
        '''
        `name` - choice name (`str`)

        `value` - choice value (`str` | `int`)
        '''
        self.name = name
        self.value = value


class Option:
    def __init__(self, name: str, description: str, type: int, required: bool=False, choices: List[OptionChoice]=None, options: list=None):
        '''
        `name` - option name

        `description` - option description

        `type` - the option type (see table below)

        `choices` - list of option choices (type <`OptionChoice`>)
        
        # Option Types
        ```json
        +-------------------+-------+
        | NAME              | VALUE |
        +-------------------+-------+
        | SUB_COMMAND       | 1     |
        | SUB_COMMAND_GROUP | 2     |
        | STRING            | 3     |
        | INTEGER           | 4     |
        | BOOLEAN           | 5     |
        | USER              | 6     |
        | CHANNEL           | 7     |
        | ROLE              | 8     |
        +-------------------+-------+
        ```
        # About option order
        Option of type `2` can only contain options of type `1`

        Option of type `1` can only contain options of type `3` or higher

        Options of type `3` and higher can't contain any sub options

        Do not specify `required=True` in case you're defining a type-1 or type-2 option
        '''
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
                        raise BadOption('Unexpected sub_command in a sub_command')
            elif self.type == 2:
                for opt in options:
                    if opt.type != 1:
                        raise BadOption('Expected sub_command in this sub_command_group')
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
                    raise BadOption('Sub_command (or group) can only be folded in a sub_command_group')
            elif self.type == 2:
                if option.type != 1:
                    raise BadOption('Expected sub_command in this sub_command_group')
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
    def __init__(self, name: str, description: str, options: list=[], *, id: int=None, application_id: int=None):
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
        self.id = id
        self.application_id = application_id
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


#-----------------------------------+
#      Slash-commands client        |
#-----------------------------------+
class SlashCommandResponse:
    def __init__(self, func):
        self.is_from_cog = '.' in func.__qualname__
        self.func = func
        self.checks = []


class SlashClient:
    def __init__(self, client):
        '''
        # Extension that allows to work with slash-commands
        ## Example
        ```
        # Importing libs
        import discord
        from discord.ext import commands
        from dislash.slash_commands import *

        # Init both <commands.Bot> and <SlashClient> instances
        client = commands.Bot(command_prefix='!', intents=discord.Intents.default())
        slash_client = SlashClient(client)

        # Define a simple slash-command response function
        @slash_client.command(name='user-info')
        async def user_info(inter: Interaction):
            # Expensive stuff here
        ```
        '''
        self.client = client
        self.events = {}
        self.commands = {}
        self.registered_global_commands = {}
        self.registered_guild_commands = {}
        self.is_ready = False
        self.client.loop.create_task(self._do_ignition())
    
    def event(self, func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'<{func.__qualname__}> must be a coroutine function')
        name = func.__name__
        if name.startswith('on_'):
            name = name[3:]
            if name in ['slash_command_error']:
                self.events[name] = func
        return func

    def command(self, *args, **kwargs):
        '''
        A decorator that registers a function below as response for specified slash-command

        `name` - name of the slash-command you want to response to
        (equals to function name by default)

        ## Example 
        ```
        @slash_client.command(name='user-info')
        async def user_info(interaction):
            # Your code
        ```
        '''
        def decorator(func):
            if not asyncio.iscoroutinefunction(func):
                raise TypeError(f'<{func.__qualname__}> must be a coroutine function')
            name = kwargs.get('name', func.__name__)
            self.commands[name] = SlashCommandResponse(func)
            return func
        return decorator
    
    def check(self, predicate):
        def decorator(func):
            name = None
            for kw, scr in self.commands.items():
                if scr.func == func:
                    name = kw
                    break
            if name is not None:
                self.commands[name].checks.append(predicate)
            return func
        return decorator
    
    def is_guild_owner(self):
        def predicate(interaction):
            if interaction.member.id == interaction.guild.owner_id:
                return True
            raise NotGuildOwner("You don't own this guild")
        return self.check(predicate)
    
    def has_permissions(self, **kwargs):
        def predicate(inter):
            if inter.member.id == inter.guild.owner_id:
                return True
            has = inter.member.guild_permissions
            if has.administrator:
                return True
            if all(getattr(has, kw, v) == v for kw, v in kwargs.items()):
                return True
            raise MissingPermissions([])
        return self.check(predicate)

    # Working with slash-commands
    async def fetch_global_commands(self):
        data = await self.client.http.request(Route('GET', '/applications/{app_id}/commands', app_id=self.client.user.id))
        return [SlashCommand.from_dict(dat) for dat in data]

    async def fetch_guild_commands(self, guild_id: int):
        data = await self.client.http.request(
            Route('GET', '/applications/{app_id}/guilds/{guild_id}/commands',
            app_id=self.client.user.id, guild_id=guild_id)
        )
        return [SlashCommand.from_dict(dat) for dat in data]
    
    async def fetch_global_command(self, command_id: int):
        data = await self.client.http.request(
            Route('GET', '/applications/{app_id}/commands/{cmd_id}',
            app_id=self.client.user.id, cmd_id=command_id)
        )
        return SlashCommand.from_dict(data)

    async def fetch_guild_command(self, guild_id: int, command_id: int):
        data = await self.client.http.request(
            Route('GET', '/applications/{app_id}/guilds/{guild_id}/commands/{cmd_id}',
            app_id=self.client.user.id, guild_id=guild_id, cmd_id=command_id)
        )
        return SlashCommand.from_dict(data)

    async def register_global_slash_command(self, slash_command: SlashCommand):
        if not isinstance(slash_command, SlashCommand):
            raise NotSlashCommand('Expected <SlashCommand> instance')
        await self.client.http.request(
            Route('POST', '/applications/{app_id}/commands', app_id=self.client.user.id),
            json=slash_command.to_dict()
        )
    
    async def register_guild_slash_command(self, guild_id: int, slash_command: SlashCommand):
        if not isinstance(slash_command, SlashCommand):
            raise NotSlashCommand('Expected <SlashCommand> instance')
        await self.client.http.request(
            Route(
                'POST', '/applications/{app_id}/guilds/{guild_id}/commands',
                app_id=self.client.user.id, guild_id=guild_id
            ),
            json=slash_command.to_dict()
        )
    
    async def edit_global_slash_command(self, command_id: int, slash_command: SlashCommand):
        if not isinstance(slash_command, SlashCommand):
            raise NotSlashCommand('Expected <SlashCommand> instance')
        await self.client.http.request(
            Route(
                'PATCH', '/applications/{app_id}/commands/{cmd_id}',
                app_id=self.client.user.id, cmd_id=command_id
            ),
            json=slash_command.to_dict()
        )
    
    async def edit_guild_slash_command(self, guild_id: int, command_id: int, slash_command: SlashCommand):
        if not isinstance(slash_command, SlashCommand):
            raise NotSlashCommand('Expected <SlashCommand> instance')
        await self.client.http.request(
            Route(
                'PATCH', '/applications/{app_id}/guilds/{guild_id}/commands/{cmd_id}',
                app_id=self.client.user.id, guild_id=guild_id, cmd_id=command_id
            ),
            json=slash_command.to_dict()
        )
    
    async def delete_global_slash_command(self, command_id: int):
        await self.client.http.request(
            Route(
                'DELETE', '/applications/{app_id}/commands/{cmd_id}',
                app_id=self.client.user.id, cmd_id=command_id
            )
        )
    
    async def delete_guild_slash_command(self, guild_id: int, command_id: int):
        await self.client.http.request(
            Route(
                'DELETE', '/applications/{app_id}/guilds/{guild_id}/commands/{cmd_id}',
                app_id=self.client.user.id, guild_id=guild_id, cmd_id=command_id
            )
        )

    # Internal use only
    async def _do_ignition(self):
        '''# Don't use it'''
        while self.client.user is None:
            await asyncio.sleep(1)
        self.is_ready = True
        self._interactions_tracker.start()
        self.registered_global_commands = await self.fetch_global_commands()
    @tasks.loop()
    async def _interactions_tracker(self):
        '''
        # Don't use it
        '''
        payload = await self.client.ws.wait_for('INTERACTION_CREATE', lambda data: True)
        self.client.loop.create_task(self._invoke_slash_command(payload))

    async def _invoke_slash_command(self, payload):
        '''
        # Don't use it
        '''
        name = payload['data']['name']
        SCR = self.commands.get(name)
        if SCR is not None:
            inter = Interaction(self.client, payload)
            # Run checks
            err = None
            for _check in SCR.checks:
                try:
                    if not _check(inter):
                        err = SlashCommandError(f'Command <{name}> failed')
                        break
                except Exception as e:
                    err = e
                    break
            # Activate error handler in case checks failed
            if err is not None:
                func = self.events['slash_command_error']
                if '.' in func.__qualname__:
                    await func(self, inter, err)
                else:
                    await func(inter, err)
                return
            # Invoke the command
            if SCR.is_from_cog:
                await SCR.func(self, inter)
            else:
                await SCR.func(inter)