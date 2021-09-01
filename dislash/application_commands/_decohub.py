# Creating a global accumulator for decorated functions
# Also avoiding circular import
from discord import Client

class _HANDLER:
    client: Client = None # type: ignore
    slash_commands = {}
    user_commands = {}
    message_commands = {}
