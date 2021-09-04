import asyncio
from typing import Awaitable, Callable, List

from ..interactions import ContextMenuInteraction, MessageCommand, UserCommand
from ._decohub import _HANDLER
from .core import InvokableApplicationCommand, class_name

__all__ = (
    "InvokableContextMenuCommand",
    "InvokableUserCommand",
    "InvokableMessageCommand",
    "user_command",
    "message_command",
)


class InvokableContextMenuCommand(InvokableApplicationCommand):
    def __init__(self, func: Callable[..., Awaitable], *, name=None, guild_ids: List[int] = None, **kwargs):
        super().__init__(func, name=name, **kwargs)
        self.guild_ids = guild_ids
        self._cog_class_name = class_name(func)
        self._cog_name = None
        self._cog = None

    def _inject_cog(self, cog):
        self._cog = cog
        self._cog_name = cog.qualified_name

    async def invoke(self, interaction: ContextMenuInteraction):
        if interaction.data.type == 2:
            interaction.user_command = self
        elif interaction.data.type == 3:
            interaction.message_command = self
        try:
            self._prepare_cooldowns(interaction)
            await self._run_checks(interaction)
            await self._maybe_cog_call(self._cog, interaction)
        except Exception as err:
            self._dispatch_error(self._cog, interaction, err)
            raise err


class InvokableUserCommand(InvokableContextMenuCommand):
    def __init__(self, func: Callable[..., Awaitable], *, name=None, guild_ids: List[int] = None, **kwargs):
        super().__init__(func, name=name, guild_ids=guild_ids, **kwargs)
        self.registerable = UserCommand(name=self.name)


class InvokableMessageCommand(InvokableContextMenuCommand):
    def __init__(self, func: Callable[..., Awaitable], *, name=None, guild_ids: List[int] = None, **kwargs):
        super().__init__(func, name=name, guild_ids=guild_ids, **kwargs)
        self.registerable = MessageCommand(name=self.name)


def user_command(*args, **kwargs):
    """
    A decorator that allows to build a user command, visible in a context menu.

    Parameters
    ----------
    name : :class:`str`
        name of the user command you want to respond to (equals to function name by default).
    guild_ids : :class:`List[int]`
        if specified, the client will register the command in these guilds.
        Otherwise this command will be registered globally.
    """

    def decorator(func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f"<{func.__qualname__}> must be a coroutine function")
        new_func = InvokableUserCommand(func, **kwargs)
        _HANDLER.user_commands[new_func.name] = new_func
        return new_func

    return decorator


def message_command(*args, **kwargs):
    """
    A decorator that allows to build a message command, visible in a context menu.

    Parameters
    ----------
    name : :class:`str`
        name of the user command you want to respond to (equals to function name by default).
    guild_ids : :class:`List[int]`
        if specified, the client will register the command in these guilds.
        Otherwise this command will be registered globally.
    """

    def decorator(func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f"<{func.__qualname__}> must be a coroutine function")
        new_func = InvokableMessageCommand(func, **kwargs)
        _HANDLER.message_commands[new_func.name] = new_func
        return new_func

    return decorator
