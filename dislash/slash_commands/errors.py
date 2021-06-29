from discord import DiscordException


class SlashCommandError(DiscordException):
    """
    The base exception type for all slash-command related errors.

    This inherits from :exc:`discord.DiscordException`.

    This exception and exceptions inherited from it are handled
    in a special way as they are caught and passed into a special event
    from :class:`.SlashClient`, :func:`on_slash_command_error`.
    """
    def __init__(self, message=None, *args):
        if message is not None:
            # clean-up @everyone and @here mentions
            m = message.replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')
            super().__init__(m, *args)
        else:
            super().__init__(*args)


class BadArgument(SlashCommandError):
    pass
            
            
class SlashCheckFailure(SlashCommandError):
    pass


class CheckAnyFailure(SlashCheckFailure):
    def __init__(self, checks, errors):
        self.checks = checks
        self.errors = errors
        super().__init__('You do not have permission to run this command.')


class PrivateMessageOnly(SlashCheckFailure):
    def __init__(self, message=None):
        super().__init__(message or 'This command can only be used in private messages.')


class NoPrivateMessage(SlashCheckFailure):
    def __init__(self, message=None):
        super().__init__(message or 'This command cannot be used in private messages.')


class NotOwner(SlashCheckFailure):
    pass


class CommandOnCooldown(SlashCommandError):
    """Exception raised when the slash-command being invoked is on cooldown.

    This inherits from `SlashCommandError`

    ## Attributes
    
    `cooldown`: `Cooldown` (a class with attributes `rate`, `per`, and `type`)

    `retry_after`: `float` (the amount of seconds to wait before you can retry again)
    """
    def __init__(self, cooldown, retry_after):
        self.cooldown = cooldown
        self.retry_after = retry_after
        super().__init__('You are on cooldown. Try again in {:.2f}s'.format(retry_after))


class NotGuildOwner(SlashCommandError):
    pass


class MissingRole(SlashCheckFailure):
    def __init__(self, missing_role):
        self.missing_role = missing_role
        message = 'Role {0!r} is required to run this command.'.format(missing_role)
        super().__init__(message)


class BotMissingRole(SlashCheckFailure):
    def __init__(self, missing_role):
        self.missing_role = missing_role
        message = 'Bot requires the role {0!r} to run this command'.format(missing_role)
        super().__init__(message)


class MissingAnyRole(SlashCheckFailure):
    def __init__(self, missing_roles):
        self.missing_roles = missing_roles

        missing = ["'{}'".format(role) for role in missing_roles]

        if len(missing) > 2:
            fmt = '{}, or {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' or '.join(missing)

        message = "You are missing at least one of the required roles: {}".format(fmt)
        super().__init__(message)


class BotMissingAnyRole(SlashCheckFailure):
    def __init__(self, missing_roles):
        self.missing_roles = missing_roles

        missing = ["'{}'".format(role) for role in missing_roles]

        if len(missing) > 2:
            fmt = '{}, or {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' or '.join(missing)

        message = "Bot is missing at least one of the required roles: {}".format(fmt)
        super().__init__(message)


class NSFWChannelRequired(SlashCheckFailure):
    def __init__(self, channel):
        self.channel = channel
        super().__init__("Channel '{}' needs to be NSFW for this command to work.".format(channel))


class MissingPermissions(SlashCheckFailure):
    def __init__(self, missing_perms, *args):
        self.missing_perms = missing_perms

        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in missing_perms]

        if len(missing) > 2:
            fmt = '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        message = 'You are missing {} permission(s) to run this command.'.format(fmt)
        super().__init__(message, *args)


class BotMissingPermissions(SlashCheckFailure):
    def __init__(self, missing_perms, *args):
        self.missing_perms = missing_perms

        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in missing_perms]

        if len(missing) > 2:
            fmt = '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        message = 'Bot requires {} permission(s) to run this command.'.format(fmt)
        super().__init__(message, *args)
