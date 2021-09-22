from __future__ import annotations
from enum import Enum
from typing import Any, List, Optional, TypedDict, SupportsInt


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
