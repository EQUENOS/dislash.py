from typing import Any, Dict
from dislash.interactions.app_command_interaction import SlashInteraction
from discord.ext.commands.cooldowns import (
    Cooldown,
    CooldownMapping,
    BucketType
)
from discord.ext.commands.errors import ConversionError
import asyncio
import datetime
import discord
import inspect
import functools

from .errors import *
from ..interactions.application_command import OptionParam


__all__ = (
    "BucketType",
    "InvokableApplicationCommand",
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


class InvokableApplicationCommand:
    def __init__(self, func, *, name=None, **kwargs):
        self.func = func
        self.name = name or func.__name__
        self._error_handler = None
        self.auto_sync = True
        # Extract checks
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
            except Exception:
                # discord.py <= 1.6.x
                try:
                    self._buckets = CooldownMapping(cooldown) # type: ignore
                except Exception:
                    # Hopefully we never reach this
                    self._buckets: CooldownMapping = None # type: ignore
        else:
            self._buckets = cooldown
        # Add custom kwargs
        for kw, value in kwargs.items():
            if not hasattr(self, kw):
                setattr(self, kw, value)

    async def __call__(self, *args, **kwargs):
        kwargs = self._process_arguments(args[0], kwargs)
        return await self.func(*args, **kwargs)

    def _process_arguments(self, inter: SlashInteraction, kwargs: Dict[str, Any]):
        sig = inspect.signature(self.func)
        for param in sig.parameters.values():
            # fix accidental defaults
            if param.name not in kwargs or isinstance(kwargs[param.name], OptionParam):
                if isinstance(param.default, OptionParam):
                    if callable(param.default.default):
                        kwargs[param.name] = param.default.default(inter)
                    elif param.default.default is not ...:
                        kwargs[param.name] = param.default.default
                elif param.default is not inspect.Parameter.empty:
                    kwargs[param.name] = param.default
            elif param.name in kwargs and isinstance(param.default, OptionParam) and param.default.converter is not None:
                    try:
                        kwargs[param.name] = param.default.converter(inter, kwargs[param.name])
                    except Exception as e:
                        raise ConversionError(param.default.converter, e) from e # type: ignore
            
            # verify types
            if param.name in kwargs and isinstance(param.default, OptionParam) and (param.default._python_type or param.annotation):
                if not self._isinstance(kwargs[param.name], (param.default._python_type or param.annotation)):
                    error = TypeError(
                        f"Expected option {param.default.name or param.name!r} "
                        f"to be of type {param.default._python_type or param.annotation!r} but received {kwargs[param.name]!r}"
                    )
                    raise ConversionError(None, error) from error # type: ignore
            
        return kwargs

    @staticmethod
    def _isinstance(obj: Any, typ: type) -> bool:
        if issubclass(typ, discord.User):
            return isinstance(obj, (discord.User, discord.Member, discord.ClientUser))
        else:
            return isinstance(obj, typ)

    def _prepare_cooldowns(self, inter):
        if self._buckets.valid:
            dt = inter.created_at
            current = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
            bucket = self._buckets.get_bucket(inter, current)
            retry_after = bucket.update_rate_limit(current)
            if retry_after:
                raise CommandOnCooldown(bucket, retry_after)

    def _dispatch_error(self, cog, inter, error):
        asyncio.create_task(self._invoke_error_handler(cog, inter, error))

    async def _run_checks(self, inter):
        for _check in self.checks:
            if not await _check(inter):
                raise InteractionCheckFailure(f"command <{self.name}> has failed")

    async def _maybe_cog_call(self, cog, inter):
        if cog:
            return await self(cog, inter)
        else:
            return await self(inter)

    async def _invoke_error_handler(self, cog, inter, error):
        if self._error_handler is None:
            return
        if cog:
            await self._error_handler(cog, inter, error)
        else:
            await self._error_handler(inter, error)

    def error(self, func):
        """
        A decorator that makes the function below
        work as error handler for this command.
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("The local error handler must be an async function")
        self._error_handler = func
        return func

    def is_on_cooldown(self, inter):
        """
        Checks whether the slash command is currently on cooldown.

        Parameters
        -----------
        inter: :class:`SlashInteraction`
            The interaction to use when checking the commands cooldown status.

        Returns
        --------
        :class:`bool`
            A boolean indicating if the slash command is on cooldown.
        """
        if not self._buckets.valid:
            return False

        bucket = self._buckets.get_bucket(inter)
        dt = inter.created_at
        current = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
        return bucket.get_tokens(current) == 0

    def reset_cooldown(self, inter):
        """
        Resets the cooldown on this slash command.

        Parameters
        -----------
        inter: :class:`SlashInteraction`
            The interaction to reset the cooldown under.
        """
        if self._buckets.valid:
            bucket = self._buckets.get_bucket(inter)
            bucket.reset()

    def get_cooldown_retry_after(self, inter):
        """
        Retrieves the amount of seconds before this slash command can be tried again.

        Parameters
        -----------
        inter: :class:`SlashInteraction`
            The interaction to retrieve the cooldown from.

        Returns
        --------
        :class:`float`
            The amount of time left on this slash command's cooldown in seconds.
            If this is ``0.0`` then the slash command isn't on cooldown.
        """
        if self._buckets.valid:
            bucket = self._buckets.get_bucket(inter)
            dt = inter.created_at
            current = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
            return bucket.get_retry_after(current)

        return 0.0


def class_name(func):
    res = func.__qualname__[:-len(func.__name__)]
    return None if len(res) == 0 else res[:-1]


def get_class(func):
    if inspect.isfunction(func):
        cn = class_name(func)
        if cn is not None:
            mod = inspect.getmodule(func)
            return getattr(mod, str(class_name(func)), None)


def check(predicate):
    '''
    A function that converts ``predicate(interaction)`` functions
    into application command decorators

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

    '''
    if inspect.iscoroutinefunction(predicate):
        wrapper = predicate # type: ignore
    else:
        async def wrapper(ctx):
            return predicate(ctx)

    def decorator(func):
        if isinstance(func, InvokableApplicationCommand):
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

        permissions = ctx.guild.me.guild_permissions
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
        if not await ctx.bot.is_owner(ctx.author):
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
        try:
            cooldown_obj = Cooldown(rate, per, type) # type: ignore
        except Exception:
            cooldown_obj = Cooldown(rate, per)

        try:
            mapping = CooldownMapping(cooldown_obj) # type: ignore
        except Exception:
            mapping = CooldownMapping(cooldown_obj, type)

        if isinstance(func, InvokableApplicationCommand):
            func._buckets = mapping
        else:
            func.__slash_cooldown__ = mapping

        return func
    return decorator
