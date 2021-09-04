# Creating a global accumulator for decorated functions
# Also avoiding circular import
# there's no saving this, just annotate everything as Any and leave it be
from typing import Any, Dict
from discord import Client


class _HANDLER:
    client: Client = None  # type: ignore
    slash_commands: Dict[str, Any] = {}
    user_commands: Dict[str, Any] = {}
    message_commands: Dict[str, Any] = {}
