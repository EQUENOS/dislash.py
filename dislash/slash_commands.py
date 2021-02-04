import discord
from discord.http import Route
from discord.ext.commands.cooldowns import Cooldown, CooldownMapping, BucketType
import asyncio
from .interactions import Interaction, SlashCommand
import datetime


#-----------------------------------+
#              Utils                |
#-----------------------------------+
def class_name(func):
    res = func.__qualname__[:-len(func.__name__)]
    return None if len(res) == 0 else res[:-1]


class PseudoCog:
    def __init__(self, client):
        '''
        A shitty solution for slash-commands in cogs
        '''
        self.client = client


class HANDLER:
    '''
    # Internal use only
    ## A global SLashCommand handler
    This is done in order to give an ability to
    decorate functions across multiple files
    ```
    from dislash import slash_commands

    @slash_commands.command()
    async def hello(interaction):
        await interaction.reply('Hi')
    ```
    ### Note that you should init `SlashClient` to track `interaction_create` events
    '''
    client = None
    commands = {}


class SlashCommandResponse:
    def __init__(self, client, func, name):
        cogname = class_name(func)
        if cogname is not None:
            self.cog = PseudoCog(client)
        else:
            self.cog = None
        if hasattr(func, '__slash_checks__'):
            self.checks = func.__slash_checks__
        else:
            self.checks = []
        try:
            cooldown = func.__slash_cooldown__
        except AttributeError:
            cooldown = None
        finally:
            self._buckets = CooldownMapping(cooldown)
        self.name = name
        self.func = func
    
    async def __call__(self, interaction):
        if self.cog is not None:
            return await self.func(self.cog, interaction)
        else:
            return await self.func(interaction)
    
    async def invoke(self, interaction):
        self._prepare_cooldowns(interaction)
        await self(interaction)

    def _prepare_cooldowns(self, inter):
        if self._buckets.valid:
            dt = inter.created_at
            current = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
            bucket = self._buckets.get_bucket(inter, current)
            retry_after = bucket.update_rate_limit(current)
            if retry_after:
                raise CommandOnCooldown(bucket, retry_after)


#-----------------------------------+
#            Exceptions             |
#-----------------------------------+
class SlashCommandError(discord.DiscordException):
    pass


class CommandOnCooldown(SlashCommandError):
    """Exception raised when the slash-command being invoked is on cooldown.

    This inherits from `SlashCommandError`

    ## Attributes
    
    `cooldown`: `Cooldown` (a class with attributes `rate`, `per`, and `type`)

    `retry_after`: `float` (the amount of seconds to wait before you can retry again)
    """
    def __init__(self, cooldown, retry_after):
        self.cooldown = cooldown
        self.retry_after = retry_after
        super().__init__('You are on cooldown. Try again in {:.2f}s'.format(retry_after))


class NotGuildOwner(SlashCommandError):
    pass


class MissingGuildPermissions(SlashCommandError):
    def __init__(self, perms):
        self.perms = perms


class MissingPermissions(SlashCommandError):
    def __init__(self, perms):
        self.perms = perms


#-----------------------------------+
#            Decorators             |
#-----------------------------------+
def command(*args, **kwargs):
    '''
    A decorator that registers a function below as response for specified slash-command

    `name` - name of the slash-command you want to respond to
    (equals to function name by default)

    (defaults to `None`, in this case function responds to
    both global and local commands with the same names)

    ## Example 
    ```
    @slash_commands.command(name='user-info')
    async def user_info(interaction):
        # Your code
    ```
    '''
    def decorator(func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'<{func.__qualname__}> must be a coroutine function')
        name = kwargs.get('name', func.__name__)
        # is_global = kwargs.get('global')
        new_func = SlashCommandResponse(HANDLER.client, func, name)
        HANDLER.commands[name] = new_func
        return new_func
    return decorator


def check(predicate):
    '''
    A function that converts `predicate(interaction)` functions
    into slash-command decorators
    '''
    def decorator(func):
        if isinstance(func, SlashCommandResponse):
            func.checks.append(predicate)
        else:
            if not hasattr(func, '__slash_checks__'):
                func.__slash_checks__ = []
            func.__slash_checks__.append(predicate)
        return func
    return decorator


def is_guild_owner():
    def predicate(interaction):
        if interaction.member.id == interaction.guild.owner_id:
            return True
        raise NotGuildOwner("You don't own this guild")
    return check(predicate)


def has_guild_permissions(**perms):
    def predicate(inter):
        if inter.member.id == inter.guild.owner_id:
            return True
        has = inter.member.guild_permissions
        if has.administrator:
            return True
        if all(getattr(has, kw, True) for kw in perms):
            return True
        raise MissingGuildPermissions([kw for kw in perms if getattr(has, kw, None) is not None])
    return check(predicate)


def has_permissions(**perms):
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError('Invalid permission(s): %s' % (', '.join(invalid)))
    def predicate(inter):
        ch = inter.channel
        permissions = ch.permissions_for(inter.member)
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]
        if not missing:
            return True
        raise MissingPermissions(missing)
    return check(predicate)


def cooldown(rate, per, type=BucketType.default):
    '''
    A decorator that adds a cooldown to a `SlashCommand`

    A cooldown allows a command to only be used a specific amount
    of times in a specific time frame. These cooldowns can be based
    either on a per-guild, per-channel, per-user, per-role or global basis.
    Denoted by the third argument of `type` which must be of enum
    type `BucketType`.

    If a cooldown is triggered, then `.CommandOnCooldown` is triggered in
    `on_slash_command_error` and the local error handler.

    A command can only have a single cooldown.

    ## Parameters
    
    `rate`: `int` - The number of times a command can be used before triggering a cooldown.

    `per`: `float`- The amount of seconds to wait for a cooldown when it's been triggered.

    `type`: `BucketType` - The type of cooldown to have.
    '''
    def decorator(func):
        if isinstance(func, SlashCommandResponse):
            func._buckets = CooldownMapping(Cooldown(rate, per, type))
        else:
            func.__slash_cooldown__ = Cooldown(rate, per, type)
        return func
    return decorator


#-----------------------------------+
#      Slash-commands client        |
#-----------------------------------+
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
        HANDLER.client = client
        self.client = HANDLER.client
        self.events = {}
        self.registered_global_commands = {}
        self.registered_guild_commands = {}
        self.is_ready = False
        self.client.loop.create_task(self._do_ignition())
    @property
    def commands(self):
        return HANDLER.commands

    def event(self, func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'<{func.__qualname__}> must be a coroutine function')
        name = func.__name__
        if name.startswith('on_'):
            name = name[3:]
            if name in ['slash_command_error', 'ready']:
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
            new_func = SlashCommandResponse(self.client, func, name)
            self.commands[name] = new_func
            return new_func
        return decorator
    
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
            raise ValueError('Expected <SlashCommand> instance')
        await self.client.http.request(
            Route('POST', '/applications/{app_id}/commands', app_id=self.client.user.id),
            json=slash_command.to_dict()
        )
    
    async def register_guild_slash_command(self, guild_id: int, slash_command: SlashCommand):
        if not isinstance(slash_command, SlashCommand):
            raise ValueError('Expected <SlashCommand> instance')
        await self.client.http.request(
            Route(
                'POST', '/applications/{app_id}/guilds/{guild_id}/commands',
                app_id=self.client.user.id, guild_id=guild_id
            ),
            json=slash_command.to_dict()
        )
    
    async def edit_global_slash_command(self, command_id: int, slash_command: SlashCommand):
        if not isinstance(slash_command, SlashCommand):
            raise ValueError('Expected <SlashCommand> instance')
        await self.client.http.request(
            Route(
                'PATCH', '/applications/{app_id}/commands/{cmd_id}',
                app_id=self.client.user.id, cmd_id=command_id
            ),
            json=slash_command.to_dict()
        )
    
    async def edit_guild_slash_command(self, guild_id: int, command_id: int, slash_command: SlashCommand):
        if not isinstance(slash_command, SlashCommand):
            raise ValueError('Expected <SlashCommand> instance')
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
        self.client.ws._discord_parsers['INTERACTION_CREATE'] = self._do_invokation
        self.is_ready = True
        self.client.loop.create_task(self._activate_event('ready'))
        self.registered_global_commands = await self.fetch_global_commands()
    
    def _do_invokation(self, payload):
        '''
        # Don't use it
        '''
        self.client.loop.create_task(self._invoke_slash_command(payload))

    async def _activate_event(self, event_name, *args, **kwargs):
        '''
        # Don't use it
        '''
        func = self.events.get(event_name)
        if func is not None:
            cogname = class_name(func)
            if cogname is not None:
                await func(PseudoCog(self.client), *args, **kwargs)
            else:
                await func(*args, **kwargs)

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
                if 'slash_command_error' not in self.events:
                    raise err
                await self._activate_event('slash_command_error', inter, err)
                return
            # Invoke the command
            try:
                await SCR.invoke(inter)
            except Exception as err:
                if 'slash_command_error' not in self.events:
                    raise err
                await self._activate_event('slash_command_error', inter, err)