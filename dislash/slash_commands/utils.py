from datetime import datetime, timedelta
import asyncio
import discord

from ._decohub import _HANDLER


__all__ = ("ClickListener", "ClickManager")


PER_MESSAGE_LISTENERS = {}


async def _on_button_click(inter):
    redir = PER_MESSAGE_LISTENERS.get(inter.message.id)
    if redir is not None:
        redir._toggle_listeners(inter)


class ClickListener:
    """
    Creates a nice click manager for a message. You can use this class,
    or call :class:`discord.Message.create_click_listener(timeout)`
    in order to create an instance.

    Click manager allows to process button clicks under a specific message
    using decorator-based interface.

    Parameters
    ----------
    message_id : :class:`int`
        the ID of the message with buttons
    timeout : :class:`float`
        the amount of seconds required after the last matched interaction
        for the click manager to finish working.
        Defaults to ``None``, which means no timeout.
    """

    __slots__ = ("id", "_listeners", "_timeout_waiter", "_timeout", "_ends_at")

    def __init__(self, message_id: int, timeout: float=None):
        self.id = message_id
        self._listeners = []
        self._timeout_waiter = None
        self._timeout = timeout
        PER_MESSAGE_LISTENERS[message_id] = self
        # Launch a finishing task
        if timeout is not None:
            self._ends_at = datetime.now() + timedelta(seconds=timeout)
            _HANDLER.client.loop.create_task(self._wait_and_finish())
        else:
            self._ends_at = None
    
    async def _wait_and_finish(self):
        delay = self._timeout
        while True:
            await asyncio.sleep(delay)
            now = datetime.now()
            if self._ends_at > now:
                delay = (self._ends_at - now).total_seconds()
            else:
                break
        PER_MESSAGE_LISTENERS.pop(self.id, None)
        if self._timeout_waiter is not None:
            await self._timeout_waiter()

    def _toggle_listeners(self, inter):
        task_toggled = False
        for listener, condition, cancel_others, reset_timeout in self._listeners:
            try:
                res = condition(inter)
            except Exception:
                res = False
            if res:
                task_toggled = task_toggled or reset_timeout
                _HANDLER.client.loop.create_task(listener(inter))
                if cancel_others:
                    break
        # Delay more
        if task_toggled and self._ends_at is not None:
            self._ends_at = datetime.now() + timedelta(seconds=self._timeout)

    def kill(self):
        """
        Kills the click manager. Only useful if the ``timeout``
        param was specified as ``None``.
        """
        self._timeout_waiter = None # Also kills the timeout waiter
        PER_MESSAGE_LISTENERS.pop(self.id, None)

    def timeout(self, func):
        """
        A decorator that makes the function below waiting for click listener timeout.
        """
        if not asyncio.iscoroutinefunction(func):
            async def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            new_func = wrapper
        else:
            new_func = func
        self._timeout_waiter = new_func

    def matching_condition(self, check, *, cancel_others: bool=False, reset_timeout: bool=True):
        """
        A decorator that makes the function below waiting for a click
        matching the specified conditions.

        Parameters
        ----------
        check : :class:`function`
            the required condition. This function must take exactly one argument
            which is guaranteed to be an instance of :class:`MessageInteraction`.
            This function must return ``True`` or ``False``.
        cancel_others : :class:`bool`
            defaults to ``False``. Specifies
            whether to cancel all other local listeners or not.
            For example, if this parameter is ``False``, the library will
            activate all other listeners matching the interaction,
            untill all listeners are toggled or some of them cancels others.
        reset_timeout : :class:`bool`
            defaults to ``True``. Specifies whether to restart the timer or not.
            By restarting the timer, you extend the lifespan of all local listeners.
        """
        def deco(func):
            if not asyncio.iscoroutinefunction(func):
                async def wrapper(*args, **kwargs):
                    return func(*args, **kwargs)
                new_func = wrapper
            else:
                new_func = func
            self._listeners.append((new_func, check, cancel_others, reset_timeout))
            return func
        return deco

    def from_user(self, user: discord.User, *, cancel_others: bool=False, reset_timeout: bool=True):
        """
        A decorator that makes the function below waiting for a click
        from the specified user.

        Parameters are the same as in :meth:`matching_condition`, except
        ``check`` parameter is replaced with a ``user`` to compare with.
        """
        def is_user(inter):
            return inter.author == user
        return self.matching_condition(
            is_user,
            cancel_others=cancel_others,
            reset_timeout=reset_timeout
        )

    def not_from_user(self, user: discord.User, *, cancel_others: bool=False, reset_timeout: bool=True):
        """
        A decorator that makes the function below waiting for a click
        from a user not maching the specified one.

        Parameters are the same as in :meth:`matching_condition`, except
        ``check`` parameter is replaced with a ``user`` to compare with.
        """
        def is_not_user(inter):
            return inter.author != user
        return self.matching_condition(
            is_not_user,
            cancel_others=cancel_others,
            reset_timeout=reset_timeout
        )

    def no_checks(self, *, cancel_others: bool=False, reset_timeout: bool=True):
        """
        A decorator that makes the function below waiting for any click.

        Parameters are the same as in :meth:`matching_condition`, except
        there's no ``check``.
        """
        def always(inter):
            return True
        return self.matching_condition(
            always,
            cancel_others=cancel_others,
            reset_timeout=reset_timeout
        )

    def matching_id(self, custom_id: str, *, cancel_others: bool=False, reset_timeout: bool=True):
        """
        A decorator that makes the function below waiting for a click
        of the button matching the specified custom_id.

        Parameters are the same as in :meth:`matching_condition`, except
        ``check`` parameter is replaced with ``custom_id``.
        """
        check = lambda inter: inter.component.custom_id == custom_id
        return self.matching_condition(
            check,
            cancel_others=cancel_others,
            reset_timeout=reset_timeout
        )


ClickManager = ClickListener
