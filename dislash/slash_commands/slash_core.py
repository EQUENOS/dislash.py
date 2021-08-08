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
from .slash_command import SlashCommand, Option, Type
from ._decohub import _HANDLER


__all__ = (
    "BucketType",
    "SubCommand",
    "SubCommandGroup",
    "CommandParent",
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
class BaseSlashCommand:
    def __init__(self, func, *, name=None, connectors=None, **kwargs):
        self.func = func
        self.name = name or func.__name__
        self.connectors = connectors
        self._error_handler = None
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
            except:
                # discord.py <= 1.6.x
                try:
                    self._buckets = CooldownMapping(cooldown)
                except:
                    # Hopefully we never reach this
                    self._buckets = None
        else:
            self._buckets = cooldown
        # Add custom kwargs
        for kw, value in kwargs.items():
            if not hasattr(self, kw):
                setattr(self, kw, value)
    
    async def __call__(self, *args, **kwargs):
        return await self.func(*args, **kwargs)

    def _uses_ui(self, from_cog: bool):
        func = inspect.unwrap(self.func)
        code = func.__code__
        argcount = code.co_argcount + code.co_kwonlyargcount
        if from_cog:
            return argcount > 2
        else:
            return argcount > 1

    def _prepare_cooldowns(self, inter):
        if self._buckets.valid:
            dt = inter.created_at
            current = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
            bucket = self._buckets.get_bucket(inter, current)
            retry_after = bucket.update_rate_limit(current)
            if retry_after:
                raise CommandOnCooldown(bucket, retry_after)

    def _dispatch_error(self, cog, inter, error):
        _HANDLER.client.loop.create_task(self._invoke_error_handler(cog, inter, error))

    async def _run_checks(self, ctx):
        for _check in self.checks:
            if not await _check(ctx):
                raise SlashCheckFailure(f"command <{self.name}> has failed")

    async def _maybe_cog_call(self, cog, inter, data):
        if self._uses_ui(cog):
            params = data._to_dict_values(self.connectors)
        else:
            params = {}
        if cog:
            return await self(cog, inter, **params)
        else:
            return await self(inter, **params)

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


class SubCommand(BaseSlashCommand):
    def __init__(self, func, *, name=None, description=None, options=None, connectors=None, **kwargs):
        super().__init__(func, name=name, connectors=connectors, **kwargs)
        self.option = Option(
            name=self.name,
            description=description or "-",
            type=Type.SUB_COMMAND,
            options=options
        )


class SubCommandGroup(BaseSlashCommand):
    def __init__(self, func, *, name=None, **kwargs):
        super().__init__(func, name=name, **kwargs)
        self.children = {}
        self.option = Option(
            name=self.name,
            description="-",
            type=Type.SUB_COMMAND_GROUP,
            options=[]
        )

    def sub_command(self, name: str=None, description: str=None, options: list=None, connectors: dict=None, **kwargs):
        """
        A decorator that creates a subcommand in the
        subcommand group.

        Parameters are the same as in :class:`CommandParent.sub_command`
        """
        def decorator(func):
            new_func = SubCommand(
                func,
                name=name,
                description=description,
                options=options,
                connectors=connectors,
                **kwargs
            )
            self.children[new_func.name] = new_func
            self.option.options.append(new_func.option)
            return new_func
        return decorator


class CommandParent(BaseSlashCommand):
    def __init__(self, func, *, name=None, description=None, options=None, default_permission=True,
                                                             guild_ids=None, connectors=None,
                                                             auto_sync=True, **kwargs):
        super().__init__(func, name=name, connectors=connectors, **kwargs)
        self.children = {}
        self.auto_sync = auto_sync
        self.registerable = SlashCommand(
            name=self.name,
            description=description or "-",
            options=options or [],
            default_permission=default_permission,
        )
        self.guild_ids = guild_ids
        self.child_type = None
        # Cog indication
        self._cog_class_name = class_name(func)
        self._cog_name = None
        self._cog = None

    def _inject_cog(self, cog):
        self._cog = cog
        self._cog_name = cog.qualified_name

    def sub_command(self, name: str=None, description: str=None, options: list=None, connectors: dict=None, **kwargs):
        """
        A decorator that creates a subcommand under the base command.

        Parameters
        ----------
        name : :class:`str`
            the name of the subcommand. Defaults to the function name
        description : :class:`str`
            the description of the subcommand
        options : :class:`list`
            the options of the subcommand for registration in API
        connectors : :class:`dict`
            which function param states for each option. If the name
            of an option already matches the corresponding function param,
            you don't have to specify the connectors. Connectors template: 
            ``{"option-name": "param_name", ...}``
        """
        def decorator(func):
            if self.child_type is None:
                if len(self.registerable.options) > 0:
                    self.registerable.options = []
                self.child_type = Type.SUB_COMMAND
            
            new_func = SubCommand(
                func,
                name=name,
                description=description,
                options=options,
                connectors=connectors,
                **kwargs
            )
            self.children[new_func.name] = new_func
            self.registerable.options.append(new_func.option)
            return new_func
        return decorator
    
    def sub_command_group(self, name=None, **kwargs):
        """
        A decorator that creates a subcommand group under the base command.
        Remember that the group must have at least one subcommand.

        Parameters
        ----------
        name : :class:`str`
            the name of the subcommand group. Defaults to the function name
        """
        def decorator(func):
            if self.child_type is None:
                if len(self.registerable.options) > 0:
                    self.registerable.options = []
                self.child_type = Type.SUB_COMMAND_GROUP
            
            new_func = SubCommandGroup(func, name=name, **kwargs)
            self.children[new_func.name] = new_func
            self.registerable.options.append(new_func.option)
            return new_func
        return decorator
    
    async def invoke_children(self, interaction):
        data = interaction.data
        
        option = data.option_at(0)
        if option is None:
            return
        
        group = None
        subcmd = None
        if option.type == Type.SUB_COMMAND_GROUP:
            group = self.children.get(option.name)
        elif option.type == Type.SUB_COMMAND:
            subcmd = self.children.get(option.name)
        
        if group is not None:
            option = option.option_at(0)
            if option is None:
                subcmd = None
            else:
                subcmd = group.children.get(option.name)
        
        if group is not None:
            interaction.invoked_with += f" {group.name}"
            interaction.sub_command_group = group
            try:
                group._prepare_cooldowns(interaction)
                await group._run_checks(interaction)
                await group._maybe_cog_call(self._cog, interaction, data)
            except Exception as err:
                group._dispatch_error(self._cog, interaction, err)
                raise err
        
        if subcmd is not None:
            interaction.invoked_with += f" {subcmd.name}"
            interaction.sub_command = subcmd
            try:
                subcmd._prepare_cooldowns(interaction)
                await subcmd._run_checks(interaction)
                await subcmd._maybe_cog_call(self._cog, interaction, option)
            except Exception as err:
                subcmd._dispatch_error(self._cog, interaction, err)
                raise err

    async def invoke(self, interaction):
        interaction._wrap_choices(self.registerable)
        interaction.slash_command = self
        try:
            self._prepare_cooldowns(interaction)
            await self._run_checks(interaction)
            await self._maybe_cog_call(self._cog, interaction, interaction.data)
            await self.invoke_children(interaction)
        except Exception as err:
            self._dispatch_error(self._cog, interaction, err)
            raise err


def command(*args, **kwargs):
    """
    A decorator that allows to build a slash command.

    Parameters
    ----------
    auto_sync : :class:`bool`
        whether to automatically register the command or not. Defaults to ``True``
    name : :class:`str`
        name of the slash command you want to respond to (equals to function name by default).
    description : :class:`str`
        the description of the slash command. It will be visible in Discord.
    options : :class:`List[Option]`
        the list of slash command options. The options will be visible in Discord.
    default_permission : :class:`bool`
        whether the command is enabled by default when the app is added to a guild.
    guild_ids : :class:`List[int]`
        if specified, the client will register a command in these guilds.
        Otherwise this command will be registered globally.
    connectors : :class:`dict`
        which function param states for each option. If the name
        of an option already matches the corresponding function param,
        you don't have to specify the connectors. Connectors template: 
        ``{"option-name": "param_name", ...}``
    """
    def decorator(func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'<{func.__qualname__}> must be a coroutine function')
        new_func = CommandParent(func, **kwargs)
        _HANDLER.commands[new_func.name] = new_func
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
        if isinstance(func, CommandParent):
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
            cooldown_obj = Cooldown(rate, per, type)
        except Exception:
            cooldown_obj = Cooldown(rate, per)
        
        try:
            mapping = CooldownMapping(cooldown_obj)
        except Exception:
            mapping = CooldownMapping(cooldown_obj, type)
        
        if isinstance(func, BaseSlashCommand):
            func._buckets = mapping
        else:
            func.__slash_cooldown__ = mapping
        
        return func
    return decorator
