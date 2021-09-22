from __future__ import annotations
from enum import Enum
from typing import Any, List, Optional, TypedDict, SupportsInt


class OptionType(int, Enum):
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


class ApplicationCommandType(int, Enum):
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
