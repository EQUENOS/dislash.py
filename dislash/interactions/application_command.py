from __future__ import annotations
import re
import typing
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, Hashable, List, Optional, TypeVar, Union

import discord

from .app_command_interaction import SlashInteraction
from .types import (
    ApplicationCommandPayload,
    ApplicationCommandPermissionsPayload,
    ApplicationCommandType,
    OptionChoicePayload,
    OptionPayload,
    OptionType,
    RawCommandPermissionPayload,
    SlashCommandPayload,
)

__all__ = (
    "application_command_factory",
    "ApplicationCommandType",
    "ApplicationCommand",
    "SlashCommand",
    "UserCommand",
    "MessageCommand",
    "OptionChoice",
    "Option",
    "OptionParam",
    "option_enum",
    "ApplicationCommandPermissions",
    "SlashCommandPermissions",
    "RawCommandPermission",
    "Type",
)

T_StrFloat = TypeVar('T_StrFloat', str, float)


def application_command_factory(data: ApplicationCommandPayload) -> ApplicationCommand:
    cmd_type = data.get("type", 1)
    if cmd_type == ApplicationCommandType.CHAT_INPUT:
        data = typing.cast(SlashCommandPayload, data)
        return SlashCommand.from_dict(data)
    elif cmd_type == ApplicationCommandType.USER:
        return UserCommand.from_dict(data)
    elif cmd_type == ApplicationCommandType.MESSAGE:
        return MessageCommand.from_dict(data)
    else:
        raise ValueError("Invalid command type")


class OptionChoice:
    """
    Parameters
    ----------
    name : str
        the name of the option-choice (visible to users)
    value : str or int
        the value of the option-choice
    """

    name: str
    value: Any

    def __init__(self, name: str, value: Any) -> None:
        self.name = name
        self.value = value

    def __repr__(self) -> str:
        return "<OptionChoice name='{0.name}' value={0.value}>".format(self)

    def __eq__(self, other):  # type: ignore
        return self.name == other.name and self.value == other.value


class Option:
    """
    Parameters
    ----------
    name : :class:`str`
        option's name
    description : :class:`str`
        option's description
    type : :class:`Type`
        the option type, e.g. ``Type.USER``, see :ref:`option_type`
    required : :class:`bool`
        whether this option is required or not
    choices : List[:class:`OptionChoice`]
        the list of option choices, type :ref:`option_choice`
    options : List[:class:`Option`]
        the list of sub options. You can only specify this parameter if
        the ``type`` is :class:`Type.SUB_COMMAND` or :class:`Type.SUB_COMMAND_GROUP`
    """

    __slots__ = ("name", "description", "type", "required", "choices", "options", "_choice_connectors")

    name: str
    description: Optional[str]
    type: int
    required: bool
    choices: List[OptionChoice]
    options: List[Option]

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        type: int = 3,
        required: bool = False,
        choices: Optional[List[OptionChoice]] = None,
        options: Optional[List[Option]] = None,
    ) -> None:
        assert name.islower(), f"Option name {name!r} must be lowercase"
        self.name = name
        self.description = description
        self.type = type
        self.required = required
        self.choices = choices or []
        if options is not None:
            if self.type == 1:
                for option in options:
                    if option.type < 3:
                        raise ValueError("Unexpected sub_command in a sub_command")
            elif self.type == 2:
                for option in options:
                    if option.type != 1:
                        raise ValueError("Expected sub_command in this sub_command_group")
        self.options = options or []
        self._choice_connectors: Dict[Union[int, str], Any] = {}
        # Wrap choices
        for i, choice in enumerate(self.choices):
            if self.type == Type.INTEGER:
                if not isinstance(choice.value, int):
                    self._choice_connectors[i] = choice.value
                    choice.value = i
            elif self.type == Type.STRING:
                if not isinstance(choice.value, str):
                    valid_value = f"option_choice_{i}"
                    self._choice_connectors[valid_value] = choice.value
                    choice.value = valid_value

    def __repr__(self) -> str:
        string = "name='{0.name}' description='{0.description}' type={0.type} required={0.required}".format(self)
        if self.options:
            string += " options={self.options}"
        if self.choices:
            string += " choices={self.choices}"
        return f"<Option {string}>"

    def __eq__(self, other):  # type: ignore
        return (
            self.name == other.name
            and self.description == other.description
            and self.type == other.type
            and self.required == other.required
            and self.choices == other.choices
            and self.options == other.options
        )

    @classmethod
    def from_dict(cls, payload: OptionPayload) -> Option:
        return Option(
            name=payload["name"],
            description=payload["description"],
            type=payload["type"],
            required=payload.get("required", False),
            options=[
                Option.from_dict(p) for p
                in payload.get("options", ())
            ],
            choices=[
                OptionChoice(**p) for p
                in payload.get("choices", ())
            ],
        )

    def add_choice(self, name: str, value: Any) -> None:
        """
        Adds an OptionChoice to the list of current choices

        Parameters are the same as for :class:`OptionChoice`
        """
        # Wrap the value
        true_value = value
        if self.type == Type.STRING:
            if not isinstance(value, str):
                true_value = f"option_choice_{len(self._choice_connectors)}"
                self._choice_connectors[true_value] = value
        elif self.type == Type.INTEGER:
            if not isinstance(value, int):
                true_value = len(self._choice_connectors)
                self._choice_connectors[true_value] = value
        # Add an option choice
        self.choices.append(OptionChoice(name=name, value=true_value))

    def add_option(
        self,
        name: str,
        description: Optional[str] = None,
        type: int = 3,
        required: bool = False,
        choices: Optional[List[OptionChoice]] = None,
        options: Optional[List[Option]] = None,
    ) -> None:
        """
        Adds an option to the current list of options

        Parameters are the same as for :class:`Option`
        """
        if self.type == 1:
            if type < 3:
                raise ValueError("sub_command can only be nested in a sub_command_group")
        elif self.type == 2:
            if type != 1:
                raise ValueError("Expected sub_command in this sub_command_group")
        self.options.append(
            Option(name=name, description=description, type=type, required=required, choices=choices, options=options)
        )

    def to_dict(self) -> OptionPayload:
        return OptionPayload(
            name=self.name,
            description=self.description,
            type=self.type,
            required=self.required,
            choices=[
                OptionChoicePayload(name=choice.name, value=choice.value)
                for choice in self.choices
            ],
            options=[
                option.to_dict() for
                option in self.options
            ],
        )


class OptionParam:
    """
    Parameters
    ----------
    default : Union[:class:`str`, Callable[[:class:`SlashInteraction`, Any], Any]]
        default value or a default value factory
    name : :class:`str`
        option's name, the parameter name by default
    description : :class:`str`
        option's description
    converter : Callable[[:class:`SlashInteraction`, Any], Any]
        the option's converter, takes in an interaction and the argument
    """

    TYPES: Dict[Hashable, int] = {
        str: 3,
        int: 4,
        bool: 5,
        discord.abc.User: 6,
        discord.User: 6,
        discord.Member: 6,
        discord.abc.GuildChannel: 7,
        discord.TextChannel: 7,
        discord.VoiceChannel: 7,
        discord.CategoryChannel: 7,
        discord.StageChannel: 7,
        discord.StoreChannel: 7,
        discord.Role: 8,
        Union[discord.Member, discord.Role]: 9,
        discord.abc.Snowflake: 9,
        float: 10,
    }

    default: Any = ...
    name: Optional[str]
    description: str
    converter: Optional[Callable[[SlashInteraction, Any], Any]]

    def __init__(
        self,
        default: Any = ...,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        converter: Optional[Callable[[SlashInteraction, Any], Any]] = None,
    ) -> None:
        self.default = default
        self.name = name
        self.description = description or "-"
        self.converter = converter

    @property
    def required(self) -> bool:
        return self.default is ...

    def __repr__(self) -> str:
        string = "default={0.default} name='{0.name}' description='{0.description}'".format(self)
        return f"<Option {string}>"


def option_param(
    default: Any = ...,
    *,
    name: Optional[str] = None,
    desc: Optional[str] = None,
    description: Optional[str] = None,
    converter: Optional[Callable[[SlashInteraction, Any], Any]] = None,
) -> OptionParam:
    if desc is not None and description is not None:
        raise TypeError("Only desc or description may be used, not both")
    return OptionParam(default, name=name, description=desc or description, converter=converter)


def option_enum(choices: Dict[str, T_StrFloat], **kwargs: T_StrFloat) -> Enum:
    choices = choices or kwargs
    return Enum('', choices, type=type(next(iter(choices.values()))))


class ApplicationCommand(ABC):
    """
    Base class for application commands
    """

    id: int
    name: str
    type: ApplicationCommandType
    application_id: Optional[int] = None

    def __init__(self, type: ApplicationCommandType, **kwargs: Any) -> None:
        self.type = type
        self.id = int(kwargs.get("id", 0))
        application_id = kwargs.get("application_id")
        if application_id is not None:
            self.application_id = int(application_id)
        else:
            self.application_id = application_id

    def __eq__(self, _):  # type: ignore
        return False

    @abstractmethod
    def to_dict(self) -> ApplicationCommandPayload:
        raise NotImplementedError


class UserCommand(ApplicationCommand):
    def __init__(self, name: str, **kwargs: Any) -> None:
        kwargs.pop('type', 0)
        super().__init__(ApplicationCommandType.USER, **kwargs)
        self.name = name

    def __repr__(self) -> str:
        return f"<UserCommand name={self.name!r}>"

    def __eq__(self, other):  # type: ignore
        return self.type == other.type and self.name == other.name

    def to_dict(self) -> ApplicationCommandPayload:
        return {"type": self.type, "name": self.name}

    @classmethod
    def from_dict(cls, data: ApplicationCommandPayload) -> UserCommand:
        if data.get("type", 1) == ApplicationCommandType.USER:
            return UserCommand(**data)
        else:
            raise ValueError(f"{cls.__name__} type can be only {ApplicationCommandType.USER}")


class MessageCommand(ApplicationCommand):
    def __init__(self, name: str, **kwargs: Any) -> None:
        kwargs.pop('type', 0)
        super().__init__(ApplicationCommandType.MESSAGE, **kwargs)
        self.name = name

    def __repr__(self) -> str:
        return f"<MessageCommand name={self.name!r}>"

    def __eq__(self, other):  # type: ignore
        return self.type == other.type and self.name == other.name

    def to_dict(self) -> ApplicationCommandPayload:
        return {"type": self.type, "name": self.name}

    @classmethod
    def from_dict(cls, data: ApplicationCommandPayload) -> MessageCommand:
        if data.get("type", 0) == ApplicationCommandType.MESSAGE:
            return MessageCommand(**data)
        else:
            raise ValueError(f"{cls.__name__} type can be only {ApplicationCommandType.MESSAGE}")


class SlashCommand(ApplicationCommand):
    """
    A base class for building slash-commands.

    Parameters
    ----------
    name : :class:`str`
        The command name
    description : :class:`str`
        The command description (it'll be displayed by discord)
    options : List[Option]
        The options of the command. See :ref:`option`
    default_permission : :class:`bool`
        Whether the command is enabled by default when the app is added to a guild
    """

    options: List[Option]
    default_permission: bool
    permissions: SlashCommandPermissions

    def __init__(
        self,
        name: str,
        description: str,
        options: Optional[List[Option]] = None,
        default_permission: bool = True,
        **kwargs: Any,
    ) -> None:
        kwargs.pop('type', 0)
        super().__init__(ApplicationCommandType.CHAT_INPUT, **kwargs)

        assert (
            re.match(r"^[\w-]{1,32}$", name) is not None and name.islower()
        ), f"Slash command name {name!r} should consist of these symbols: a-z, 0-9, -, _"

        self.name = name
        self.description = description
        self.options = options or []
        self.default_permission = default_permission
        self.permissions = SlashCommandPermissions()

    def __repr__(self) -> str:
        return "<SlashCommand name='{0.name}' description='{0.description}' options={0.options}>".format(self)

    def __eq__(self, other):  # type: ignore
        return (
            self.type == other.type
            and self.name == other.name
            and self.description == other.description
            and self.options == other.options
        )

    @classmethod
    def from_dict(cls, payload: SlashCommandPayload) -> SlashCommand:
        if payload.get("type", 1) != ApplicationCommandType.CHAT_INPUT:
            raise ValueError(f"{cls.__name__} type can be only {ApplicationCommandType.CHAT_INPUT}")

        options = payload.pop("options", [])
        return SlashCommand(
            id=payload["id"],
            name=payload["name"],
            description=payload["description"],
            type=payload["type"],
            default_permission=payload.get("default_permission", True),
            options=[
                Option.from_dict(p) for p in options
            ],
        )

    def add_option(
        self,
        name: str,
        description: Optional[str] = None,
        type: int = 3,
        required: bool = False,
        choices: Optional[List[OptionChoice]] = None,
        options: Optional[List[Option]] = None,
    ) -> None:
        """
        Adds an option to the current list of options

        Parameters are the same as for :class:`Option`
        """
        self.options.append(
            Option(
                name=name,
                description=description,
                type=type,
                required=required,
                choices=choices,
                options=options
            )
        )

    def to_dict(self, *, hide_name: bool = False) -> SlashCommandPayload:
        res: SlashCommandPayload = {
            "type": self.type,
            "description": self.description,
            "options": [o.to_dict() for o in self.options],
        }
        if not self.default_permission:
            res["default_permission"] = False
        if not hide_name:
            res["name"] = self.name
        return res


# Permissions
class ApplicationCommandPermissions:
    """
    Represents application command permissions.
    Roughly equivalent to a list of :class:`RawCommandPermission`

    Application command permissions are checked on the server side.
    Only local application commands can have this type of permissions.

    Parameters
    ----------
    raw_permissions : List[RawCommandPermission]
        a list of :class:`RawCommandPermission`.
        However, :meth:`from_pairs` or :meth:`from_ids`
        might be more convenient.
    """

    permissions: List[RawCommandPermission]

    def __init__(self, raw_permissions: Optional[List[RawCommandPermission]] = None) -> None:
        self.permissions = raw_permissions or []

    def __repr__(self) -> str:
        return "<{0.__name__} permissions={0.permissions!r}>".format(self)

    @classmethod
    def from_pairs(cls, permissions: Dict[Union[discord.Role, discord.User], bool]) -> ApplicationCommandPermissions:
        """
        Creates :class:`ApplicationCommandPermissions` using
        instances of :class:`discord.Role` and :class:`discord.User`

        Parameters
        ----------
        permissions : :class:`dict`
            a dictionary of {:class:`Role | User`: :class:`bool`}
        """
        raw_perms = [RawCommandPermission.from_pair(target, perm) for target, perm in permissions.items()]

        return ApplicationCommandPermissions(raw_perms)

    @classmethod
    def from_ids(
        cls,
        role_perms: Optional[Dict[int, bool]] = None,
        user_perms: Optional[Dict[int, bool]] = None,
    ) -> ApplicationCommandPermissions:
        """
        Creates :class:`ApplicationCommandPermissions` from
        2 dictionaries of IDs and permissions.

        Parameters
        ----------
        role_perms : :class:`dict`
            a dictionary of {``role_id``: :class:`bool`}
        user_perms : :class:`dict`
            a dictionary of {``user_id``: :class:`bool`}
        """
        role_perms = role_perms or {}
        user_perms = user_perms or {}
        raw_perms = [RawCommandPermission(role_id, 1, perm) for role_id, perm in role_perms.items()]

        for user_id, perm in user_perms.items():
            raw_perms.append(RawCommandPermission(user_id, 2, perm))
        return ApplicationCommandPermissions(raw_perms)

    @classmethod
    def from_dict(cls, data: ApplicationCommandPermissionsPayload) -> ApplicationCommandPermissions:
        return SlashCommandPermissions([RawCommandPermission.from_dict(perm) for perm in data["permissions"]])

    def to_dict(self) -> ApplicationCommandPermissionsPayload:
        return {"permissions": [perm.to_dict() for perm in self.permissions]}


class RawCommandPermission:
    """
    Represents command permissions for a role or a user.

    Attributes
    ----------
    id : :class:`int`
        ID of a target
    type : :class:`int`
        1 if target is a role; 2 if target is a user
    permission : :class:`bool`
        allow or deny the access to the command
    """

    __slots__ = ("id", "type", "permission")

    id: int
    type: int
    permission: bool

    def __init__(self, id: int, type: int, permission: bool) -> None:
        self.id = id
        self.type = type
        self.permission = permission

    def __repr__(self) -> str:
        return "<RawCommandPermission id={0.id} type={0.type} permission={0.permission}>".format(self)

    @classmethod
    def from_pair(cls, target: Union[discord.Role, discord.User], permission: bool) -> RawCommandPermission:
        if not isinstance(target, (discord.Role, discord.User)):
            raise discord.InvalidArgument("target should be Role or User")
        if not isinstance(permission, bool):
            raise discord.InvalidArgument("permission should be bool")
        return RawCommandPermission(
            id=target.id, type=1 if isinstance(target, discord.Role) else 2, permission=permission
        )

    @classmethod
    def from_dict(cls, data: RawCommandPermissionPayload) -> RawCommandPermission:
        return RawCommandPermission(**data)

    def to_dict(self) -> RawCommandPermissionPayload:
        return {"id": self.id, "type": self.type, "permission": self.permission}


Type = OptionType
SlashCommandPermissions = ApplicationCommandPermissions
