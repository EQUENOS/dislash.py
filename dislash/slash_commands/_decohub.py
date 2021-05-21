# Creating a global accumulator for decorated functions
# Also avoiding circular import
class _HANDLER:
    client = None
    commands = {}
