from typing import Any, List, Optional, TypedDict


class OptionChoicePayload(TypedDict):
    name: str
    value: Any


class OptionPayload(TypedDict, total=False):
    name: str
    description: Optional[str]
    required: bool
    type: int
    choices: List[OptionChoicePayload]
    options: List["OptionPayload"]  # type: ignore
