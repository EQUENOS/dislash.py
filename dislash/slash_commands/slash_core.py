from discord.ext.commands.cooldowns import (
    Cooldown,
    CooldownMapping,
    BucketType
)
import asyncio
import datetime
import discord
import inspect
import functools

from .errors import *
from .slash_command import SlashCommand
from ._decohub import _HANDLER


__all__ = (
    "BucketType",
    "SlashCommandResponse",
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
)


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


#-----------------------------------+
#         Core and checks           |
#-----------------------------------+
class SlashCommandResponse:
    def __init__(self, client, func, name: str, description: str=None,
                options: list=None, default_permission: bool=True,
                guild_ids: list=None):
        self.client = client
        if hasattr(func, '__slash_checks__'):
            self.checks = func.__slash_checks__
        else:
            self.checks = []
        # Cooldown
        try:
            cooldown = func.__slash_cooldown__
        except AttributeError:
            cooldown = None
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
        else:
            self._buckets = cooldown
        
        self.name = name
        self.func = func
        self.guild_ids = guild_ids
        if description is not None:
            self.registerable = SlashCommand(name, description, options, default_permission)
        elif options is not None:
            raise SyntaxError('<options> require <description> specified')
        else:
            self.registerable = None
        self._auto_merged = False
        # Cog indication
        self._cog_class_name = class_name(func)
        self._cog_name = None
        self.__cog = None
    
    async def __call__(self, interaction):
        if self.__cog is not None:
            return await self.func(self.__cog, interaction)
        else:
            return await self.func(interaction)
    
    async def invoke(self, interaction):
        self._prepare_cooldowns(interaction)
        await self._run_checks(interaction)
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
        self._cog_name = cog.qualified_name

    async def _run_checks(self, ctx):
        for _check in self.checks:
            if not await _check(ctx):
                raise SlashCheckFailure(f"command <{self.name}> has failed")


def command(*args, **kwargs):
    '''
    A decorator that registers a function below as response for specified slash-command.

    Parameters are similar to SlashCommand arguments.

    If ``description`` is specified, the decorator will be interpreted as SlashCommand and
    will be registered (or edited) automatically with the given set of arguments.

    Parameters
    ----------
    name : str
        name of the slash-command you want to respond to (equals to function name by default)
    description : str
        if specified, the client will automatically register a command with this description
    options : List[Option]
        if specified, the client will
        automatically register a command with this list of options. Requires ``description``
    default_permission : :class:`bool`
        whether the command is enabled by default when the app is added to a guild.
        Requires ``description``
    guild_ids : List[int]
        if specified, the client will register a command in these guilds.
        Otherwise this command will be registered globally. Requires ``description``
    '''
    def decorator(func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'<{func.__qualname__}> must be a coroutine function')
        name = kwargs.get('name', func.__name__)
        new_func = SlashCommandResponse(
            _HANDLER.client, func, name,
            kwargs.get('description'),
            kwargs.get('options'),
            kwargs.get("default_permission", True),
            kwargs.get('guild_ids')
        )
        _HANDLER.commands[name] = new_func
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
            except SlashCheckFailure as e:
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
            func.__slash_cooldown__ = CooldownMapping(Cooldown(rate, per, type))
        return func
    return decorator

