from discord.http import Route
from discord.shard import AutoShardedClient
from discord.ext.commands.cooldowns import Cooldown, CooldownMapping, BucketType
from discord.ext.commands.errors import CommandError
from discord.errors import Forbidden
from .interactions import Interaction, SlashCommand
import discord as discord
import asyncio as asyncio
import datetime as datetime
import inspect, functools


__all__ = [
    "SlashClient",
    "SlashCommandResponse",
    "SlashCommandError",
    "CheckFailure",
    "PrivateMessageOnly",
    "NoPrivateMessage",
    "NotOwner",
    "CommandOnCooldown",
    "NotGuildOwner",
    "MissingRole",
    "BotMissingRole",
    "BotMissingAnyRole",
    "NSFWChannelRequired",
    "MissingPermissions",
    "BotMissingPermissions",
    "command",
    "check",
    "check_any",
    "has_role",
    "has_any_role",
    "bot_has_role",
    "bot_has_any_role",
    "has_permissions",
    "bot_has_permissions",
    "has_guild_permissions",
    "bot_has_guild_permissions",
    "dm_only",
    "guild_only",
    "is_owner",
    "is_nsfw",
    "cooldown"
]


#-----------------------------------+
#              Utils                |
#-----------------------------------+
def class_name(func):
    res = func.__qualname__[:-len(func.__name__)]
    return None if len(res) == 0 else res[:-1]


def get_class(func):
    if inspect.isfunction(func):
        cn = class_name(func)
        if cn is not None:
            mod = inspect.getmodule(func)
            return getattr(mod, class_name(func), None)


class HANDLER:
    '''
    Internal use only
    -----------------
    '''
    client = None
    commands = {}


class SlashCommandResponse:
    def __init__(self, client, func, name: str, description: str=None, options: list=None, guild_ids: list=None):
        self.client = client
        if hasattr(func, '__slash_checks__'):
            self.checks = func.__slash_checks__
        else:
            self.checks = []
        try:
            cooldown = func.__slash_cooldown__
        except AttributeError:
            cooldown = None
        finally:
            if cooldown is None:
                try:
                    # Assuming that it's discord.py 1.7.0+
                    self._buckets = CooldownMapping(cooldown, BucketType.default)
                except:
                    # discord.py <= 1.6.x
                    try:
                        self._buckets = CooldownMapping(cooldown)
                    except:
                        # Hopefully we never reach this
                        self._buckets = None
            elif isinstance(cooldown, CooldownMapping):
                self._buckets = cooldown
        self.name = name
        self.func = func
        self.guild_ids = guild_ids
        if description is not None:
            self.registerable = SlashCommand(name, description, options)
        elif options is not None:
            raise SyntaxError('<options> require <description> specified')
        else:
            self.registerable = None
        self._auto_merged = False
        # Cog indication
        self._cog_name = class_name(func)
        self.__cog = None
    
    async def __call__(self, interaction):
        if self.__cog is not None:
            return await self.func(self.__cog, interaction)
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

    def _inject_cog(self, cog):
        self.__cog = cog

    async def _run_checks(self, ctx):
        for _check in self.checks:
            if not await _check(ctx):
                raise CheckFailure(f"command <{self.name}> has failed")

#-----------------------------------+
#            Exceptions             |
#-----------------------------------+
SlashCommandError = CommandError

class CheckFailure(SlashCommandError):
    pass

class CheckAnyFailure(CheckFailure):
    def __init__(self, checks, errors):
        self.checks = checks
        self.errors = errors
        super().__init__('You do not have permission to run this command.')

class PrivateMessageOnly(CheckFailure):
    def __init__(self, message=None):
        super().__init__(message or 'This command can only be used in private messages.')

class NoPrivateMessage(CheckFailure):
    def __init__(self, message=None):
        super().__init__(message or 'This command cannot be used in private messages.')

class NotOwner(CheckFailure):
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

class MissingRole(CheckFailure):
    def __init__(self, missing_role):
        self.missing_role = missing_role
        message = 'Role {0!r} is required to run this command.'.format(missing_role)
        super().__init__(message)

class BotMissingRole(CheckFailure):
    def __init__(self, missing_role):
        self.missing_role = missing_role
        message = 'Bot requires the role {0!r} to run this command'.format(missing_role)
        super().__init__(message)

class MissingAnyRole(CheckFailure):
    def __init__(self, missing_roles):
        self.missing_roles = missing_roles

        missing = ["'{}'".format(role) for role in missing_roles]

        if len(missing) > 2:
            fmt = '{}, or {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' or '.join(missing)

        message = "You are missing at least one of the required roles: {}".format(fmt)
        super().__init__(message)

class BotMissingAnyRole(CheckFailure):
    def __init__(self, missing_roles):
        self.missing_roles = missing_roles

        missing = ["'{}'".format(role) for role in missing_roles]

        if len(missing) > 2:
            fmt = '{}, or {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' or '.join(missing)

        message = "Bot is missing at least one of the required roles: {}".format(fmt)
        super().__init__(message)

class NSFWChannelRequired(CheckFailure):
    def __init__(self, channel):
        self.channel = channel
        super().__init__("Channel '{}' needs to be NSFW for this command to work.".format(channel))

class MissingPermissions(CheckFailure):
    def __init__(self, missing_perms, *args):
        self.missing_perms = missing_perms

        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in missing_perms]

        if len(missing) > 2:
            fmt = '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        message = 'You are missing {} permission(s) to run this command.'.format(fmt)
        super().__init__(message, *args)

class BotMissingPermissions(CheckFailure):
    def __init__(self, missing_perms, *args):
        self.missing_perms = missing_perms

        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in missing_perms]

        if len(missing) > 2:
            fmt = '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        message = 'Bot requires {} permission(s) to run this command.'.format(fmt)
        super().__init__(message, *args)

#-----------------------------------+
#            Decorators             |
#-----------------------------------+

def command(*args, **kwargs):
    '''
    A decorator that registers a function below as response for specified slash-command.

    Parameters are similar to SlashCommand arguments.

    If ``description`` is specified, the decorator will be interpreted as SlashCommand and
    will be registered (or edited) automatically with the given set of arguments.

    Parameters
    ----------
    name : str
        (optional) name of the slash-command you want to respond to (equals to function name by default)
    description : str
        (optional) if specified, the client will automatically register a command with this description
    options : List[Option]
        (optional) if specified, the client will
        automatically register a command with this list of options. Requires ``description``
    guild_ids : List[int]
        (optional) if specified, the client will register a command in these guilds.
        Otherwise this command will be registered globally. Requires ``description``
    '''
    def decorator(func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'<{func.__qualname__}> must be a coroutine function')
        name = kwargs.get('name', func.__name__)
        new_func = SlashCommandResponse(
            HANDLER.client, func, name,
            kwargs.get('description'),
            kwargs.get('options'),
            kwargs.get('guild_ids')
        )
        HANDLER.commands[name] = new_func
        return new_func
    return decorator

def check(predicate):
    '''
    A function that converts ``predicate(interaction)`` functions
    into slash-command decorators

    Example

    ::

        def is_guild_owner():
            def predicate(inter):
                return inter.author.id == inter.guild.owner_id
            return check(predicate)
        
        @is_guild_owner()
        @slash.command(description="Says Hello if you own the guild")
        async def hello(inter):
            await inter.reply("Hello, Mr.Owner!")
    
    .. note::
        
        | In this example registration of slash-command is automatic.
        | See :ref:`slash-command_constructor` to learn more about manual registration
    
    '''
    if inspect.iscoroutinefunction(predicate):
        wrapper = predicate
    else:
        async def wrapper(ctx):
            return predicate(ctx)
    def decorator(func):
        if isinstance(func, SlashCommandResponse):
            func.checks.append(wrapper)
        else:
            if not hasattr(func, '__slash_checks__'):
                func.__slash_checks__ = []
            func.__slash_checks__.append(wrapper)
        return func
    decorator.predicate = wrapper
    return decorator

def check_any(*checks):
    """Similar to ``commands.check_any``"""

    unwrapped = []
    for wrapped in checks:
        try:
            pred = wrapped.predicate
        except AttributeError:
            raise TypeError('%r must be wrapped by commands.check decorator' % wrapped) from None
        else:
            unwrapped.append(pred)

    async def predicate(ctx):
        errors = []
        for func in unwrapped:
            try:
                value = await func(ctx)
            except CheckFailure as e:
                errors.append(e)
            else:
                if value:
                    return True
        # if we're here, all checks failed
        raise CheckAnyFailure(unwrapped, errors)

    return check(predicate)

def has_role(item):
    """Similar to ``commands.has_role``"""

    def predicate(ctx):
        if not isinstance(ctx.channel, discord.abc.GuildChannel):
            raise NoPrivateMessage()

        if isinstance(item, int):
            role = discord.utils.get(ctx.author.roles, id=item)
        else:
            role = discord.utils.get(ctx.author.roles, name=item)
        if role is None:
            raise MissingRole(item)
        return True

    return check(predicate)

def has_any_role(*items):
    """Similar to ``commands.has_any_role``"""
    def predicate(ctx):
        if not isinstance(ctx.channel, discord.abc.GuildChannel):
            raise NoPrivateMessage()

        getter = functools.partial(discord.utils.get, ctx.author.roles)
        if any(getter(id=item) is not None if isinstance(item, int) else getter(name=item) is not None for item in items):
            return True
        raise MissingAnyRole(items)

    return check(predicate)

def bot_has_role(item):
    """Similar to ``commands.bot_has_role``"""

    def predicate(ctx):
        ch = ctx.channel
        if not isinstance(ch, discord.abc.GuildChannel):
            raise NoPrivateMessage()

        me = ch.guild.me
        if isinstance(item, int):
            role = discord.utils.get(me.roles, id=item)
        else:
            role = discord.utils.get(me.roles, name=item)
        if role is None:
            raise BotMissingRole(item)
        return True
    return check(predicate)

def bot_has_any_role(*items):
    """Similar to ``commands.bot_has_any_role``"""
    def predicate(ctx):
        ch = ctx.channel
        if not isinstance(ch, discord.abc.GuildChannel):
            raise NoPrivateMessage()

        me = ch.guild.me
        getter = functools.partial(discord.utils.get, me.roles)
        if any(getter(id=item) is not None if isinstance(item, int) else getter(name=item) is not None for item in items):
            return True
        raise BotMissingAnyRole(items)
    return check(predicate)

def has_permissions(**perms):
    """Similar to ``commands.has_permissions``"""

    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError('Invalid permission(s): %s' % (', '.join(invalid)))

    def predicate(ctx):
        ch = ctx.channel
        permissions = ch.permissions_for(ctx.author)

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise MissingPermissions(missing)

    return check(predicate)

def bot_has_permissions(**perms):
    """Similar to ``commands.bot_has_permissions``"""

    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError('Invalid permission(s): %s' % (', '.join(invalid)))

    def predicate(ctx):
        guild = ctx.guild
        me = guild.me if guild is not None else ctx.bot.user
        permissions = ctx.channel.permissions_for(me)

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise BotMissingPermissions(missing)

    return check(predicate)

def has_guild_permissions(**perms):
    """Similar to ``commands.has_guild_permissions``"""

    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError('Invalid permission(s): %s' % (', '.join(invalid)))

    def predicate(ctx):
        if not ctx.guild:
            raise NoPrivateMessage

        permissions = ctx.author.guild_permissions
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise MissingPermissions(missing)

    return check(predicate)

def bot_has_guild_permissions(**perms):
    """Similar to ``commands.bot_has_guild_permissions``"""

    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError('Invalid permission(s): %s' % (', '.join(invalid)))

    def predicate(ctx):
        if not ctx.guild:
            raise NoPrivateMessage

        permissions = ctx.me.guild_permissions
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise BotMissingPermissions(missing)

    return check(predicate)

def dm_only():
    """Similar to ``commands.dm_only``"""

    def predicate(ctx):
        if ctx.guild is not None:
            raise PrivateMessageOnly()
        return True

    return check(predicate)

def guild_only():
    """Similar to ``commands.guild_only``"""

    def predicate(ctx):
        if ctx.guild is None:
            raise NoPrivateMessage()
        return True

    return check(predicate)

def is_owner():
    """Similar to ``commands.is_owner``"""

    async def predicate(ctx):
        if not await ctx.client.is_owner(ctx.author):
            raise NotOwner('You do not own this bot.')
        return True

    return check(predicate)

def is_nsfw():
    """Similar to ``commands.is_nsfw``"""
    def pred(ctx):
        ch = ctx.channel
        if ctx.guild is None or (isinstance(ch, discord.TextChannel) and ch.is_nsfw()):
            return True
        raise NSFWChannelRequired(ch)
    return check(pred)

def cooldown(rate, per, type=BucketType.default):
    '''
    A decorator that adds a cooldown to a slash-command. Similar to **discord.py** cooldown decorator.

    A cooldown allows a command to only be used a specific amount
    of times in a specific time frame. These cooldowns can be based
    either on a per-guild, per-channel, per-user, per-role or global basis.
    Denoted by the third argument of ``type`` which must be of enum
    type ``BucketType``.

    If a cooldown is triggered, then ``CommandOnCooldown`` is triggered in
    ``on_slash_command_error`` in the local error handler.

    A command can only have a single cooldown.

    Parameters
    ----------
    rate : int
        The number of times a command can be used before triggering a cooldown.
    per : float
        The amount of seconds to wait for a cooldown when it's been triggered.
    type : BucketType
        The type of cooldown to have.
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
    '''
    The main purpose of this class is to track ``INTERACTION_CREATE`` API event.

    Parameters
    ----------
    client : :class:`commands.Bot` | :class:`commands.AutoShardedBot`

    Attributes
    ----------
    client : :class:`commands.Bot` | :class:`commands.AutoShardedBot`
    registered_global_commands : dict
        All registered global commands are cached here
    is_ready : bool
        Equals to ``True`` if SlashClient is ready, otherwise it's ``False``
    '''
    def __init__(self, client):
        HANDLER.client = client
        self.client = HANDLER.client
        self.events = {}
        self.registered_global_commands = []
        self.registered_guild_commands = {}
        self.active_shard_count = 0
        self.is_ready = False
        self.client.add_listener(self._on_shard_connect, 'on_shard_connect')
        self.client.add_listener(self._on_connect, 'on_connect')
        # Modify cog loader
        _add_cog = self.client.add_cog
        def add_cog_2(cog):
            self._inject_cogs(cog)
            _add_cog(cog)
        self.client.add_cog = add_cog_2
        # Modify cog unloader
        _rem_cog = self.client.remove_cog
        def rem_cog_2(name):
            self._eject_cogs(name)
            _rem_cog(name)
        self.client.remove_cog = rem_cog_2
        # Link the slash ext to client
        self.client.slash = self
        # Inject cogs that are already loaded
        for cog in self.client.cogs.values():
            self._inject_cogs(cog)

    @property
    def commands(self):
        return HANDLER.commands

    def event(self, func):
        '''
        Decorator
        ::
        
            @slash.event
            async def on_ready():
                print("SlashClient is ready")
        
        | All possible events:
        | ``on_ready``, ``on_auto_register``,
        | ``on_slash_command``, ``on_slash_command_error``
        '''
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'<{func.__qualname__}> must be a coroutine function')
        name = func.__name__
        if name.startswith('on_'):
            name = name[3:]
            if name in [
                'slash_command', 'slash_command_error',
                'ready', 'auto_register'
                ]:
                self.events[name] = func
        return func

    def command(self, *args, **kwargs):
        '''
        A decorator that registers a function below as response for specified slash-command.

        Parameters are similar to SlashCommand arguments.

        If ``description`` is specified, the decorator will be interpreted as SlashCommand and
        will be registered (or edited) automatically with the given set of arguments.

        Parameters
        ----------

        name : str
            (optional) name of the slash-command you want to respond to (equals to function name by default)
        
        description : str
            (optional) if specified, the client will automatically register a command with this description
        
        options : List[Option]
            (optional) if specified, the client will
            automatically register a command with this list of options. Requires ``description``
        
        guild_ids : List[int]
            (optional) if specified, the client will register a command in these guilds.
            Otherwise this command will be registered globally. Requires ``description``
        '''
        def decorator(func):
            if not asyncio.iscoroutinefunction(func):
                raise TypeError(f'<{func.__qualname__}> must be a coroutine function')
            name = kwargs.get('name', func.__name__)
            new_func = SlashCommandResponse(
                self.client, func, name,
                kwargs.get('description'),
                kwargs.get('options'),
                kwargs.get('guild_ids')
            )
            self.commands[name] = new_func
            return new_func
        return decorator
    
    # Getters
    def get_global_command(self, command_id: int):
        """
        Get a cached global command

        Parameters
        ----------

        command_id : int
            the ID of the command
        
        Returns
        -------

        slash_command : SlashCommand | None
        """
        for cmd in self.registered_global_commands:
            if cmd.id == command_id:
                return cmd
    
    def get_global_command_named(self, name: str):
        """
        Get a cached global command matching the specified name

        Parameters
        ----------

        name : str
            the name of the command
        
        Returns
        -------

        slash_command : SlashCommand | None
        """
        for cmd in self.registered_global_commands:
            if cmd.name == name:
                return cmd

    # Straight references to API
    async def fetch_global_commands(self):
        '''Requests a list of global registered commands from the API

        Returns
        -------

        global_commands : List[SlashCommand]
        '''
        data = await self.client.http.request(Route('GET', '/applications/{app_id}/commands', app_id=self.client.user.id))
        return [SlashCommand.from_dict(dat) for dat in data]

    async def fetch_guild_commands(self, guild_id: int):
        '''Requests a list of registered commands for a specific guild

        Parameters
        ----------

        guild_id : int

        Returns
        -------

        guild_commands : List[SlashCommand]
        '''
        data = await self.client.http.request(
            Route('GET', '/applications/{app_id}/guilds/{guild_id}/commands',
            app_id=self.client.user.id, guild_id=guild_id)
        )
        return [SlashCommand.from_dict(dat) for dat in data]
    
    async def fetch_global_command(self, command_id: int):
        '''Requests a registered global slash-command

        Parameters
        ----------

        command_id : int

        Returns
        -------

        global_command : SlashCommand
        '''
        data = await self.client.http.request(
            Route('GET', '/applications/{app_id}/commands/{cmd_id}',
            app_id=self.client.user.id, cmd_id=command_id)
        )
        return SlashCommand.from_dict(data)

    async def fetch_guild_command(self, guild_id: int, command_id: int):
        '''Requests a registered guild command

        Parameters
        ----------

        guild_id : int

        command_id : int

        Returns
        -------

        guild_command : SlashCommand
        '''
        data = await self.client.http.request(
            Route('GET', '/applications/{app_id}/guilds/{guild_id}/commands/{cmd_id}',
            app_id=self.client.user.id, guild_id=guild_id, cmd_id=command_id)
        )
        return SlashCommand.from_dict(data)

    async def register_global_slash_command(self, slash_command: SlashCommand):
        '''Registers a global slash-command

        .. seealso:: :ref:`raw_slash_command`
        
        Parameters
        ----------

        slash_command : SlashCommand
        '''
        if not isinstance(slash_command, SlashCommand):
            raise ValueError('Expected <SlashCommand> instance')
        r = await self.client.http.request(
            Route('POST', '/applications/{app_id}/commands', app_id=self.client.user.id),
            json=slash_command.to_dict()
        )
        sc = SlashCommand.from_dict(r)
        self.registered_global_commands.append(sc)
        return sc
    
    async def register_guild_slash_command(self, guild_id: int, slash_command: SlashCommand):
        '''Registers a local slash-command
        
        .. seealso:: :ref:`raw_slash_command`
        
        Parameters
        ----------

        guild_id : int

        slash_command : SlashCommand
        '''
        if not isinstance(slash_command, SlashCommand):
            raise ValueError('Expected <SlashCommand> instance')
        await self.client.http.request(
            Route(
                'POST', '/applications/{app_id}/guilds/{guild_id}/commands',
                app_id=self.client.user.id, guild_id=guild_id
            ),
            json=slash_command.to_dict()
        )
    
    async def edit_global_slash_command(self, command_id: int, slash_command: SlashCommand, **kwargs):
        '''Edits a global command

        Parameters
        ----------
        command_id : int
        slash_command : SlashCommand
            replacement of the old data
        '''
        if not isinstance(slash_command, SlashCommand):
            raise discord.InvalidArgument('parameter slash_command must be SlashCommand')
        ignore_name = kwargs.get("ignore_name", False)
        r = await self.client.http.request(
            Route(
                'PATCH', '/applications/{app_id}/commands/{cmd_id}',
                app_id=self.client.user.id, cmd_id=command_id
            ),
            json=slash_command.to_dict(hide_name=ignore_name)
        )
        # Update cache
        sc = SlashCommand.from_dict(r)
        for i, cmd in enumerate(self.registered_global_commands):
            if cmd.id == command_id:
                self.registered_global_commands[i] = sc
                break
        return sc
    
    async def edit_guild_slash_command(self, guild_id: int, command_id: int, slash_command: SlashCommand, **kwargs):
        '''Edits a local command

        Parameters
        ----------
        guild_id : int
        command_id : int
        slash_command : SlashCommand
            replacement of the old data
        '''
        if not isinstance(slash_command, SlashCommand):
            raise discord.InvalidArgument('parameter slash_command must be SlashCommand')
        ignore_name = kwargs.get("ignore_name", False)
        r = await self.client.http.request(
            Route(
                'PATCH', '/applications/{app_id}/guilds/{guild_id}/commands/{cmd_id}',
                app_id=self.client.user.id, guild_id=guild_id, cmd_id=command_id
            ),
            json=slash_command.to_dict(hide_name=ignore_name)
        )
        return SlashCommand.from_dict(r)
    
    async def delete_global_slash_command(self, command_id: int):
        '''Deletes a global command

        Parameters
        ----------

        command_id : int
        '''
        for i, cmd in enumerate(self.registered_global_commands):
            if cmd.id == command_id:
                self.registered_global_commands.pop(i)
                break
        await self.client.http.request(
            Route(
                'DELETE', '/applications/{app_id}/commands/{cmd_id}',
                app_id=self.client.user.id, cmd_id=command_id
            )
        )
        # Update cache
        for i, cmd in enumerate(self.registered_global_commands):
            if cmd.id == command_id:
                self.registered_global_commands.pop(i)
                break
    
    async def delete_guild_slash_command(self, guild_id: int, command_id: int):
        '''Deletes a local command

        Parameters
        ----------

        guild_id : int

        command_id : int
        '''
        await self.client.http.request(
            Route(
                'DELETE', '/applications/{app_id}/guilds/{guild_id}/commands/{cmd_id}',
                app_id=self.client.user.id, guild_id=guild_id, cmd_id=command_id
            )
        )

    async def delete_global_commands(self, ignore_errors=False):
        """
        Deletes all global commands.

        Parameters
        ----------
        ignore_errors : bool
            if set to ``True``, the method doesn't get interrupted by unexpected errors
        """
        for cmd in self.registered_global_commands:
            try:
                await self.delete_global_command(cmd.id)
            except Exception as e:
                if not ignore_errors:
                    raise e

    async def delete_guild_commands(self, guild_id: int, ignore_errors=False):
        """
        Deletes all local commands in the specified guild.

        Parameters
        ----------
        guild_id : int
            the ID of the guild where you're going to delete the commands
        ignore_errors : bool
            if set to ``True``, the method doesn't get interrupted by unexpected errors
        """
        cmds = await self.fetch_guild_commands(guild_id)
        for cmd in cmds:
            try:
                await self.delete_guild_command(guild_id, cmd.id)
            except Exception as e:
                if not ignore_errors:
                    raise e

    # Even slower API methods
    async def fetch_global_command_named(self, name: str):
        '''
        Fetches a global command that matches the specified name

        Parameters
        ----------

        name : str
            the name of the command to fetch
        '''
        for c in self.registered_global_commands:
            if c.name == name:
                return c
        cmds = await self.fetch_global_commands()
        for c in cmds:
            if c.name == name:
                self.registered_global_commands.append(c)
                return c

    async def fetch_guild_command_named(self, guild_id: int, name: str):
        '''
        Fetches a guild command that matches the specified name

        Parameters
        ----------

        guild_id : int
            ID of the guild where the command is registered

        name : str
            the name of the command to fetch
        '''
        if guild_id in self.registered_guild_commands:
            for cmd in self.registered_guild_commands[guild_id]:
                if cmd.name == name:
                    return cmd
        cmds = await self.fetch_guild_commands(guild_id)
        self.registered_guild_commands[guild_id] = cmds
        for cmd in cmds:
            if cmd.name == name:
                return cmd

    async def edit_global_command_named(self, name: str, slash_command: SlashCommand):
        '''
        Edits a global command matching the specified name.

        Parameters
        ----------

        name : str
            the name of the command to edit
        
        slash_command : SlashCommand
            replacement of the old data
        '''
        cmd = await self.fetch_global_command_named(name)
        if cmd is not None:
            await self.edit_global_command(cmd.id, slash_command)

    async def edit_guild_command_named(self, guild_id: int, name: str, slash_command: SlashCommand):
        '''
        Edits a local command matching the specified name.

        Parameters
        ----------

        guild_id : int
            ID of the guild where the command is registered

        name : str
            the name of the command to edit
        
        slash_command : SlashCommand
            replacement of the old data
        '''
        cmd = await self.fetch_guild_command_named(guild_id, name)
        if cmd is not None:
            await self.edit_guild_command(guild_id, cmd.id, slash_command)

    async def delete_global_command_named(self, name: str):
        '''
        Deletes a global command matching the specified name.

        Parameters
        ----------

        name : str
            the name of the command to delete
        '''
        cmd = await self.fetch_global_command_named(name)
        if cmd is not None:
            await self.delete_global_command(cmd.id)

    async def delete_guild_command_named(self, guild_id: int, name: str):
        '''
        Deletes a local command matching the specified name.

        Parameters
        ----------

        guild_id : int
            ID of the guild where the command is registered

        name : str
            the name of the command to edit
        '''
        cmd = await self.fetch_guild_command_named(guild_id, name)
        if cmd is not None:
            await self.delete_guild_command(guild_id, cmd.id)

    # Internal things
    def _inject_cogs(self, cog):
        for cmd in self.commands.values():
            if cmd._cog_name == cog.__cog_name__:
                cmd._inject_cog(cog)
        if self.is_ready:
            self.client.loop.create_task(self._auto_register_or_patch())
    
    def _eject_cogs(self, name):
        HANDLER.commands = {kw: cmd for kw, cmd in HANDLER.commands.items() if cmd._cog_name != name}

    def _do_invokation(self, payload):
        '''
        # Don't use it
        '''
        self.client.loop.create_task(self._invoke_slash_command(payload))

    # Mega automated super-smart AI powered destructor-2000
    async def _auto_register_or_patch(self):
        total_posts = 0
        total_patches = 0
        bad_guilds = []
        for name, cmd in HANDLER.commands.items():
            if cmd.registerable is not None and not cmd._auto_merged:
                cmd._auto_merged = True
                # Local registration
                if cmd.guild_ids is not None:
                    # Iterate through guilds
                    for ID in cmd.guild_ids:
                        if ID in bad_guilds:
                            continue
                        # Check if the command is registered
                        try:
                            old_cmd = await self.fetch_guild_command_named(ID, cmd.name)
                            if old_cmd is None:
                                await self.register_guild_slash_command(ID, cmd.registerable)
                                total_posts += 1
                            elif not (old_cmd == cmd.registerable):
                                await self.edit_guild_slash_command(ID, old_cmd.id, cmd.registerable, ignore_name=True)
                                total_patches += 1
                        except Exception as e:
                            if isinstance(e, Forbidden):
                                bad_guilds.append(ID)
                            else:
                                print(f"[WARNING] Failed to build <{name}> in <{ID}>: {e}")
                # Global registration
                else:
                    try:
                        old_cmd = await self.fetch_global_command_named(cmd.name)
                        if old_cmd is None:
                            await self.register_global_slash_command(cmd.registerable)
                            total_posts += 1
                        elif not (old_cmd == cmd.registerable):
                            await self.edit_global_slash_command(old_cmd.id, cmd.registerable, ignore_name=True)
                            total_patches += 1
                    except Exception as e:
                        print(f"[WARNING] Failed to globally build {name}: {e}")
        
        if len(bad_guilds) > 0:
            print(f"[WARNING] Missing access: '" + "', '".join(str(ID) for ID in bad_guilds) + "'")
        
        if total_patches > 0 or total_posts > 0:
            self.client.loop.create_task(
                self._activate_event('auto_register', total_posts, total_patches)
            )

    # Adding relevant listeners
    async def _on_shard_connect(self, shard_id):
        self.client._AutoShardedClient__shards[shard_id].ws._discord_parsers['INTERACTION_CREATE'] = self._do_invokation
        self.active_shard_count += 1
        if self.active_shard_count >= self.client.shard_count:
            self.registered_global_commands = await self.fetch_global_commands()
            await self._auto_register_or_patch()
            self.is_ready = True
            await self._activate_event('ready')
    
    async def _on_connect(self):
        if not isinstance(self.client, AutoShardedClient):
            self.client.ws._discord_parsers['INTERACTION_CREATE'] = self._do_invokation
            self.registered_global_commands = await self.fetch_global_commands()
            await self._auto_register_or_patch()
            self.is_ready = True
            await self._activate_event('ready')
    
    async def _activate_event(self, event_name, *args, **kwargs):
        '''
        # Don't use it
        '''
        func = self.events.get(event_name)
        if func is not None:
            cog = get_class(func)
            if cog is not None:
                await func(cog(self.client), *args, **kwargs)
            else:
                await func(*args, **kwargs)

    async def _invoke_slash_command(self, payload):
        '''
        # Don't use it
        '''
        inter = Interaction(self.client, payload)
        # Activate event
        await self._activate_event('slash_command', inter)
        # Invoke command
        SCR = self.commands.get(inter.data.name)
        if SCR is not None:
            # Run checks
            err = None
            try:
                await SCR._run_checks(inter)
            except Exception as e:
                err = e
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
    
    # Aliases
    register_global_command = register_global_slash_command
    
    register_guild_command = register_guild_slash_command

    edit_global_command = edit_global_slash_command

    edit_guild_command = edit_guild_slash_command

    delete_global_command = delete_global_slash_command

    delete_guild_command = delete_guild_slash_command
