import asyncio
import inspect

from .core import InvokableApplicationCommand, class_name
from ..interactions import SlashCommand, Option, Type
from ._decohub import _HANDLER


__all__ = (
    "SubCommand",
    "SubCommandGroup",
    "CommandParent",
    "slash_command",
    "command"
)


class BaseSlashCommand(InvokableApplicationCommand):
    def __init__(self, func, *, name=None, connectors=None, **kwargs):
        super().__init__(func, name=name, **kwargs)
        self.connectors = connectors

    def _uses_ui(self, from_cog: bool):
        func = inspect.unwrap(self.func)
        code = func.__code__
        argcount = code.co_argcount + code.co_kwonlyargcount
        if from_cog:
            return argcount > 2
        else:
            return argcount > 1

    async def _maybe_cog_call(self, cog, inter, data):
        params = data._to_dict_values(self.connectors) if self._uses_ui(cog) else {}
        if cog:
            return await self(cog, inter, **params)
        else:
            return await self(inter, **params)


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

    def sub_command(self, name: str = None, description: str = None, options: list = None, connectors: dict = None, **kwargs):
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

    def sub_command(self, name: str = None, description: str = None, options: list = None, connectors: dict = None, **kwargs):
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
            subcmd = None if option is None else group.children.get(option.name)
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


def slash_command(*args, **kwargs):
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
        _HANDLER.slash_commands[new_func.name] = new_func
        return new_func
    return decorator


def command(*args, **kwargs):
    return slash_command(*args, **kwargs)
