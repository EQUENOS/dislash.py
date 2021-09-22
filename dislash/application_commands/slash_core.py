import asyncio
import inspect
from enum import EnumMeta
from typing import Any, Awaitable, Callable, Dict, List, Literal, Optional, Tuple, Union, get_origin

from ..interactions import (
    InteractionDataOption,
    Option,
    OptionChoice,
    SlashCommand,
    SlashInteraction,
    SlashInteractionData,
    Type,
)
from ..interactions.application_command import OptionParam
from ._decohub import _HANDLER
from .core import InvokableApplicationCommand, class_name

__all__ = ("SubCommand", "SubCommandGroup", "CommandParent", "slash_command", "command")


def fix_required(func: Callable, options: List[Option], connectors: Dict[str, str] = None) -> List[Option]:
    """Add a required to every option that doesn't have one"""
    connectors = connectors or {}

    sig = inspect.signature(func)
    for option in options:
        param = sig.parameters.get(connectors.get(option.name, option.name))
        if param is not None and not option.required and param.default is inspect.Parameter.empty:
            option.required = False
    return options


def extract_options(func: Callable) -> Tuple[List[Option], Dict[str, str]]:
    """Helper function to extract options and connectors from a function"""
    empty = inspect.Parameter.empty  # helper

    sig = inspect.signature(func)
    if "." in func.__qualname__:
        params = list(sig.parameters.values())[2:]
    else:
        params = list(sig.parameters.values())[1:]

    options = []
    connectors = {}
    for param in params:
        option_type, choices = parse_annotation(param.annotation)

        if isinstance(param.default, OptionParam):
            d = param.default
            option = Option(d.name or param.name, d.description, option_type, d.required, choices)
            if d.name is not None:
                connectors[d.name] = param.name
        else:
            option = Option(param.name, "-", type=option_type, required=param.default is empty, choices=choices)

        options.append(option)

    return options, connectors


def parse_annotation(annotation: Any) -> Tuple[int, Optional[List[OptionChoice]]]:
    """Extracts type or choices from an annotation"""
    if annotation is inspect.Parameter.empty or annotation is Any:
        return 3, None

    elif get_origin(annotation) is Literal:
        t = OptionParam.TYPES[type(annotation.__args__[0])]
        choices = [OptionChoice(str(i), i) for i in annotation.__args__]
        return t, choices

    elif isinstance(annotation, EnumMeta):
        members = [(i.name, i.value) for i in annotation]  # type: ignore
        t = OptionParam.TYPES[type(members[0][1])]
        choices = [OptionChoice(str(name).replace("_", " "), value) for name, value in members]
        return t, choices

    elif annotation in OptionParam.TYPES:
        return OptionParam.TYPES[annotation], None

    valid = ", ".join(getattr(i, "__name__", str(i)) for i in OptionParam.TYPES)
    raise TypeError(f"{annotation} is not a valid type. Must be one of: " + valid)


class BaseSlashCommand(InvokableApplicationCommand):
    def __init__(
        self, func: Callable[..., Awaitable], *, name: str = None, connectors: Dict[str, str] = None, **kwargs
    ):
        super().__init__(func, name=name, **kwargs)
        self.connectors = connectors

    def _uses_ui(self, from_cog: bool) -> bool:
        func = inspect.unwrap(self.func)
        code = func.__code__
        argcount = code.co_argcount + code.co_kwonlyargcount
        if from_cog:
            return argcount > 2
        else:
            return argcount > 1

    async def _maybe_cog_call(
        self, cog: Any, inter: SlashInteraction, data: Union[SlashInteractionData, InteractionDataOption]
    ):
        kwargs = data._to_dict_values(self.connectors) if self._uses_ui(cog) else {}
        if isinstance(self, (CommandParent, SubCommandGroup)) and self.children:
            # this fixes a bug where command parents with OptionParam recieve subcommand options
            kwargs = {}
        else:
            kwargs = self._process_arguments(inter, kwargs)

        if cog:
            return await self(cog, inter, **kwargs)
        else:
            return await self(inter, **kwargs)

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
            elif isinstance(param.default, OptionParam) and param.default.converter is not None:
                try:
                    kwargs[param.name] = param.default.converter(inter, kwargs[param.name])
                except Exception as e:
                    raise ConversionError(param.default.converter, e) from e  # type: ignore

            # verify types
            if (
                param.name in kwargs
                and isinstance(param.default, OptionParam)
                and not self._isinstance(kwargs[param.name], param.annotation)
            ):
                error = TypeError(
                    f"Expected option {param.default.name or param.name!r} "
                    f"to be of type {param.annotation!r} but received {kwargs[param.name]!r}"
                )
                raise ConversionError(None, error) from error  # type: ignore

        return kwargs


class SubCommand(BaseSlashCommand):
    def __init__(
        self,
        func: Callable[..., Awaitable],
        *,
        name: str = None,
        description: str = None,
        options: List[Option] = None,
        connectors: Dict[str, str] = None,
        **kwargs,
    ):
        super().__init__(func, name=name, connectors=connectors, **kwargs)
        if options:
            options = fix_required(func, options)
        else:
            options, connectors = extract_options(func)
            if self.connectors:
                self.connectors.update(connectors)
            else:
                self.connectors = connectors

        self.option = Option(name=self.name, description=description or "-", type=Type.SUB_COMMAND, options=options)


class SubCommandGroup(BaseSlashCommand):
    def __init__(self, func: Callable[..., Awaitable], *, name: str = None, **kwargs):
        super().__init__(func, name=name, **kwargs)
        self.children: Dict[str, SubCommand] = {}
        self.option = Option(name=self.name, description="-", type=Type.SUB_COMMAND_GROUP, options=[])

    def sub_command(
        self,
        name: str = None,
        description: str = None,
        options: List[Option] = None,
        connectors: Dict[str, str] = None,
        **kwargs,
    ):
        """
        A decorator that creates a subcommand in the
        subcommand group.

        Parameters are the same as in :class:`CommandParent.sub_command`
        """

        def decorator(func):
            new_func = SubCommand(
                func, name=name, description=description, options=options, connectors=connectors, **kwargs
            )
            self.children[new_func.name] = new_func
            self.option.options.append(new_func.option)
            return new_func

        return decorator


class CommandParent(BaseSlashCommand):
    def __init__(
        self,
        func: Callable[..., Awaitable],
        *,
        name: str = None,
        description: str = None,
        options: List[Option] = None,
        default_permission: bool = True,
        guild_ids: List[int] = None,
        connectors: Dict[str, str] = None,
        auto_sync: bool = True,
        **kwargs,
    ):
        super().__init__(func, name=name, connectors=connectors, **kwargs)
        if options:
            options = fix_required(func, options)
        else:
            options, connectors = extract_options(func)
            if self.connectors:
                self.connectors.update(connectors)
            else:
                self.connectors = connectors

        self.children: Dict[str, Union[SubCommand, SubCommandGroup]] = {}
        self.auto_sync = auto_sync
        self.registerable = SlashCommand(
            name=self.name,
            description=description or "-",
            options=options,
            default_permission=default_permission,
        )
        self.guild_ids = guild_ids
        self.child_type: Any = None
        # Cog indication
        self._cog_class_name = class_name(func)
        self._cog_name = None
        self._cog = None

    def _inject_cog(self, cog):
        self._cog = cog
        self._cog_name = cog.qualified_name

    def sub_command(
        self,
        name: str = None,
        description: str = None,
        options: List[Option] = None,
        connectors: Dict[str, str] = None,
        **kwargs,
    ):
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
                func, name=name, description=description, options=options, connectors=connectors, **kwargs
            )
            self.children[new_func.name] = new_func
            self.registerable.options.append(new_func.option)
            return new_func

        return decorator

    def sub_command_group(self, name: str = None, **kwargs):
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

    async def invoke_children(self, interaction: SlashInteraction):
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
            subcmd = None if option is None or isinstance(group, SubCommand) else group.children.get(option.name)
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

        if subcmd is not None and option is not None:
            interaction.invoked_with += f" {subcmd.name}"
            interaction.sub_command = subcmd
            try:
                subcmd._prepare_cooldowns(interaction)
                await subcmd._run_checks(interaction)
                await subcmd._maybe_cog_call(self._cog, interaction, option)
            except Exception as err:
                subcmd._dispatch_error(self._cog, interaction, err)
                raise err

    async def invoke(self, interaction: SlashInteraction):
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


def slash_command(*args, **kwargs) -> Callable[[Callable[..., Awaitable]], CommandParent]:
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
            raise TypeError(f"<{func.__qualname__}> must be a coroutine function")
        new_func = CommandParent(func, **kwargs)
        _HANDLER.slash_commands[new_func.name] = new_func
        return new_func

    return decorator


command = slash_command
