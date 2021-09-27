from __future__ import annotations
from enum import IntEnum
from typing import Any, List, Optional, TypedDict, SupportsInt, Union

from discord import PartialEmoji


__all__ = (
    'OptionType',
    'ComponentType',
    'ApplicationCommandType',
    'ButtonStyle',
)


class OptionType(IntEnum):
    """
    Attributes
    ----------
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
    NUMBER = 10
    """

    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
    NUMBER = 10


class OptionChoicePayload(TypedDict):
    name: str
    value: Any


class OptionPayload(TypedDict, total=False):
    name: str
    description: Optional[str]
    required: bool
    type: int
    choices: List[OptionChoicePayload]
    options: List[OptionPayload]  # type: ignore


class ApplicationCommandType(IntEnum):
    CHAT_INPUT = 1
    SLASH = 1
    USER = 2
    MESSAGE = 3


class ApplicationCommandPayload(TypedDict, total=False):
    id: Optional[SupportsInt]
    name: str
    type: ApplicationCommandType
    application_id: Optional[SupportsInt]


class SlashCommandPayload(ApplicationCommandPayload, total=False):
    description: str
    options: Optional[List[OptionPayload]]
    default_permission: bool


class RawCommandPermissionPayload(TypedDict):
    id: int
    type: int
    permission: bool


class ApplicationCommandPermissionsPayload(TypedDict):
    permissions: List[RawCommandPermissionPayload]


class SelectOptionPayload(TypedDict, total=False):
    label: str
    value: str
    description: Optional[str]
    emoji: Optional[Union[str, PartialEmoji]]
    default: bool


class ComponentType(IntEnum):
    """
    An enumerator for component types.

    Attributes
    ----------
    ActionRow = 1
    Button = 2
    SelectMenu = 3
    """

    ActionRow = 1
    Button = 2
    SelectMenu = 3


class ComponentPayload(TypedDict, total=False):
    disabled: bool
    custom_id: Optional[str]
    type: int


class SelectMenuPayload(ComponentPayload, total=False):
    placeholder: Optional[str]
    min_values: int
    max_values: int
    options: List[SelectOptionPayload]


class ButtonStyle(IntEnum):
    """
    Attributes
    ----------
    blurple = 1
    grey    = 2
    green   = 3
    red     = 4
    link    = 5
    """

    primary = 1
    blurple = 1

    secondary = 2
    grey = 2
    gray = 2

    success = 3
    green = 3

    danger = 4
    red = 4

    link = 5


class ButtonPayload(ComponentPayload, total=False):
    style: ButtonStyle
    label: Optional[str]
    emoji: Optional[Union[PartialEmoji, str]]
    url: Optional[str]


class ActionRowPayload(ComponentPayload):
    components: Optional[List[ComponentPayload]]
