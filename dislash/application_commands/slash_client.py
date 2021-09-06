import asyncio
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import discord
from discord import Guild
from discord.ext import commands
from discord.http import Route

from ..interactions import (
    ApplicationCommand,
    ApplicationCommandPermissions,
    BaseInteraction,
    ComponentType,
    ContextMenuInteraction,
    MessageInteraction,
    SlashCommand,
    SlashInteraction,
    application_command_factory,
)
from ._decohub import _HANDLER
from .context_menus_core import InvokableMessageCommand, InvokableUserCommand, message_command, user_command
from .slash_core import CommandParent, slash_command
from .utils import ClickListener, _on_button_click

__all__ = ("InteractionClient", "SlashClient")


class InteractionClient:
    """
    The main purpose of this class is to track ``INTERACTION_CREATE`` API event.

    Parameters
    ----------
    client : :class:`commands.Bot` | :class:`commands.AutoShardedBot`
        The discord.py Bot instance
    test_guilds : :class:`List[int]`
        A list of IDs of guilds where the application commands
        should be registered instead of global registration
    sync_commands : :class:`bool`
        If set to True, your client will sync all registered commands with the code
    show_warnings : :class:`bool`
        Whether to show the warnings or not. Defaults to ``True``
    modify_send : :class:`bool`
        Whether to modify :class:`Messageable.send` and :class:`Message.edit`.
        Modified methods allow to specify the ``components`` parameter.

    Attributes
    ----------
    client : :class:`commands.Bot` | :class:`commands.AutoShardedBot`
        an instance of any class inherited from :class:`discord.Client`
    application_id : :class:`int`
        the ID of the application your bot is related to
    global_commands : List[:class:`ApplicationCommand`]
        All registered global application commands
    slash_commands : :class:`Dict[str, CommandParent]`
        All invokable slash commands from your code
    user_commands : :class:`Dict[str, InvokableUserCommand]`
        All invokable user commands from your code
    message_commands : :class:`Dict[str, InvokableMessageCommand]`
        All invokable message commands from your code
    commands : :class:`Dict[str, InvokableApplicationCommand]`
        All invokable application commands from your code
    is_ready : bool
        Equals to ``True`` if SlashClient is ready, otherwise it's ``False``
    """

    def __init__(
        self,
        client,
        *,
        test_guilds: List[int] = None,
        sync_commands: bool = True,
        show_warnings: bool = True,
        modify_send: bool = True,
    ) -> None:
        self._uses_discord_2 = hasattr(client, "add_view")
        _HANDLER.client = client
        self.client: Any = _HANDLER.client
        self.application_id = None
        self.events: Dict[str, Callable[..., Awaitable]] = {}
        self._listeners: Dict[Any, List[Tuple[Any, Callable]]] = {}
        self._global_commands: Dict[int, ApplicationCommand] = {}
        self._guild_commands: Dict[int, Dict[int, ApplicationCommand]] = {}
        self._cogs_with_err_listeners = {
            "on_slash_command_error": [],
            "on_user_command_error": [],
            "on_message_command_error": [],
        }
        self._test_guilds = test_guilds
        self._sync_commands = sync_commands
        self._show_warnings = show_warnings
        self._modify_send = modify_send
        self.active_shard_count: int = 0
        self.is_ready: bool = False
        # Add listeners
        self._register_listeners()
        # Modify old discord.py methods
        self._modify_discord()
        # Link the slash ext to client if doesn't exist yet
        if not hasattr(self.client, "slash"):
            self.client.slash = self
        # Inject cogs that are already loaded
        for cog in self.client.cogs.values():
            self._inject_cogs(cog)

    def _register_listeners(self) -> None:
        self.client.add_listener(self._on_guild_remove, "on_guild_remove")
        self.client.add_listener(self._on_socket_response, "on_socket_response")
        if isinstance(self.client, commands.AutoShardedBot):
            self.client.add_listener(self._on_shard_connect, "on_shard_connect")
            self.client.add_listener(self._on_ready, "on_ready")
        else:
            self.client.add_listener(self._on_connect, "on_connect")
        # For nice click listener
        self.client.add_listener(_on_button_click, "on_button_click")

    def _modify_discord(self) -> None:
        # Modify cog loader
        _add_cog = self.client.add_cog

        def add_cog_2(cog):
            self._inject_cogs(cog)
            _add_cog(cog)

        self.client.add_cog = add_cog_2
        # Modify cog unloader
        _rem_cog = self.client.remove_cog

        def rem_cog_2(name):
            self._eject_cogs(name)
            _rem_cog(name)

        self.client.remove_cog = rem_cog_2
        # Multiple wait for
        self.client.multiple_wait_for = self.multiple_wait_for
        # Change other class methods

        async def ctx_wait_for_button_click(ctx, check=None, timeout=None):
            return await self.wait_for_button_click(check=check, timeout=timeout)

        async def message_wait_for_button_click(message, check=None, timeout=None):
            if check is None:
                check = lambda inter: True

            def auto_check(inter):
                if message.id != inter.message.id:
                    return False
                return check(inter)

            return await self.wait_for_button_click(auto_check, timeout)

        async def message_wait_for_dropdown(message, check=None, timeout=None):
            if check is None:
                check = lambda inter: True

            def auto_check(inter):
                if message.id != inter.message.id:
                    return False
                return check(inter)

            return await self.wait_for_dropdown(auto_check, timeout)

        async def fetch_commands(guild):
            return await self.fetch_guild_commands(guild.id)

        async def fetch_command(guild, command_id):
            return await self.fetch_guild_command(guild.id, command_id)

        async def edit_command(guild, command_id, slash_command):
            return await self.edit_guild_slash_command(guild.id, command_id, slash_command)  # type: ignore

        async def edit_command_permissions(guild, command_id, permissions):
            return await self.edit_guild_command_permissions(guild.id, command_id, permissions)

        async def batch_edit_command_permissions(guild, permissions):
            return await self.batch_edit_guild_command_permissions(guild.id, permissions)

        async def delete_command(guild, command_id):
            return await self.delete_guild_command(guild.id, command_id)

        async def delete_commands(guild):
            return await self.delete_guild_commands(guild.id)

        def get_commands(guild):
            return self.get_guild_commands(guild.id)

        def get_command(guild, command_id):
            return self.get_guild_command(guild.id, command_id)

        def get_command_named(guild, name):
            return self.get_guild_command_named(guild.id, name)

        def create_click_listener(message, timeout=None):
            return ClickListener(message.id, timeout)

        # hack to allow monkey patching by declaring a module as Any
        discord = globals()["discord"]
        commands = globals()["commands"]

        if self._modify_send:
            if self._uses_discord_2:
                from ._modifications.new import edit as edit_with_components
                from ._modifications.new import send as send_with_components
            else:
                from ._modifications.old import (
                    create_message_with_components,
                    edit_with_components,
                    send_with_components,
                )

                discord.state.create_message = create_message_with_components
            discord.abc.Messageable.send = send_with_components
            discord.Message.edit = edit_with_components

        commands.Context.wait_for_button_click = ctx_wait_for_button_click
        discord.Message.create_click_listener = create_click_listener
        discord.Message.wait_for_button_click = message_wait_for_button_click
        discord.Message.wait_for_dropdown = message_wait_for_dropdown
        discord.Guild.get_commands = get_commands
        discord.Guild.get_command = get_command
        discord.Guild.get_command_named = get_command_named
        discord.Guild.fetch_commands = fetch_commands
        discord.Guild.fetch_command = fetch_command
        discord.Guild.edit_command = edit_command
        discord.Guild.edit_command_permissions = edit_command_permissions
        discord.Guild.batch_edit_command_permissions = batch_edit_command_permissions
        discord.Guild.delete_command = delete_command
        discord.Guild.delete_commands = delete_commands

    def teardown(self) -> None:
        """Cleanup the client by removing all registered listeners and caches."""
        self.client.remove_listener(self._on_guild_remove, "on_guild_remove")
        self.client.remove_listener(self._on_socket_response, "on_socket_response")
        if isinstance(self.client, commands.AutoShardedBot):
            self.client.remove_listener(self._on_shard_connect, "on_shard_connect")
            self.client.remove_listener(self._on_ready, "on_ready")
        else:
            self.client.remove_listener(self._on_connect, "on_connect")

        self.events.clear()
        self._listeners.clear()
        self._global_commands.clear()
        self._guild_commands.clear()
        if hasattr(self.client, "slash"):
            del self.client.slash  # type: ignore
        self.is_ready = False

    @property
    def slash_commands(self) -> Dict[str, CommandParent]:
        return _HANDLER.slash_commands

    @property
    def user_commands(self) -> Dict[str, CommandParent]:
        return _HANDLER.user_commands

    @property
    def message_commands(self) -> Dict[str, CommandParent]:
        return _HANDLER.message_commands

    @property
    def commands(self) -> Dict[str, CommandParent]:
        return dict(**_HANDLER.slash_commands, **_HANDLER.user_commands, **_HANDLER.message_commands)

    @property
    def global_commands(self) -> List[ApplicationCommand]:
        return [sc for sc in self._global_commands.values()]

    def event(self, func: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
        """
        Decorator
        ::

            @slash.event
            async def on_ready():
                print("SlashClient is ready")

        | All possible events:
        | ``on_ready``, ``on_auto_register``,
        | ``on_slash_command``, ``on_slash_command_error``
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f"<{func.__qualname__}> must be a coroutine function")
        name = func.__name__
        if name.startswith("on_"):
            name = name[3:]
            self.events[name] = func
        return func

    def slash_command(self, *args, **kwargs) -> Callable[[Callable[..., Awaitable]], CommandParent]:
        """
        A decorator that allows to build a slash command.

        Parameters
        ----------
        auto_sync : :class:`bool`
            whether to automatically register the command or not. Defaults to ``True``
        name : :class:`str`
            name of the slash command you want to respond to (equals to function name by default).
        description : :class:`str`
            the description of the slash command. It will be visible in Discord.
        options : :class:`List[Option]`
            the list of slash command options. The options will be visible in Discord.
        default_permission : :class:`bool`
            whether the command is enabled by default when the app is added to a guild.
        guild_ids : :class:`List[int]`
            if specified, the client will register a command in these guilds.
            Otherwise this command will be registered globally.
        connectors : :class:`dict`
            which function param states for each option. If the name
            of an option already matches the corresponding function param,
            you don't have to specify the connectors. Connectors template:
            ``{"option-name": "param_name", ...}``
        """
        return slash_command(*args, **kwargs)

    def user_command(self, *args, **kwargs) -> Callable[[Callable[..., Awaitable]], InvokableUserCommand]:
        return user_command(*args, **kwargs)

    def message_command(self, *args, **kwargs) -> Callable[[Callable[..., Awaitable]], InvokableMessageCommand]:
        return message_command(*args, **kwargs)

    # Getters
    def get_global_command(self, command_id: int):
        """
        Get a cached global command

        Parameters
        ----------

        command_id : int
            the ID of the command

        Returns
        -------

        slash_command : SlashCommand | None
        """
        return self._global_commands.get(command_id)

    def get_global_command_named(self, name: str):
        """
        Get a cached global command matching the specified name

        Parameters
        ----------

        name : str
            the name of the command

        Returns
        -------

        slash_command : SlashCommand | None
        """
        for cmd in self._global_commands.values():
            if cmd and cmd.name == name:
                return cmd

    def get_guild_command(self, guild_id: int, command_id: int):
        """
        Get a cached guild command

        Parameters
        ----------

        guild_id : int
            the ID of the guild

        command_id : int
            the ID of the command

        Returns
        -------

        slash_command : SlashCommand | None
        """
        granula = self._guild_commands.get(guild_id)
        if granula is not None:
            return granula.get(command_id)

    def get_guild_command_named(self, guild_id: int, name: str):
        """
        Get a cached guild command matching the specified name

        Parameters
        ----------

        guild_id : int
            the ID of the guild

        name : str
            the name of the command

        Returns
        -------

        slash_command : SlashCommand | None
        """
        granula = self._guild_commands.get(guild_id)
        if granula is not None:
            for cmd in granula.values():
                if cmd.name == name:
                    return cmd

    def get_guild_commands(self, guild_id: int):
        """
        Get cached guild commands

        Parameters
        ----------
        guild_id : int
            the ID of the guild

        Returns
        -------
        ~:class:`List[ApplicationCommand]`
        """
        granula = self._guild_commands.get(guild_id, {})
        return [sc for sc in granula.values()]

    # Straight references to API
    async def fetch_global_commands(self):
        """
        Requests a list of global registered commands from the API

        Returns
        -------

        global_commands : List[ApplicationCommand]
        """
        data = await self.client.http.request(
            Route("GET", "/applications/{application_id}/commands", application_id=self.application_id)
        )
        return [application_command_factory(dat) for dat in data]

    async def fetch_guild_commands(self, guild_id: int):
        """
        Requests a list of registered commands for a specific guild

        Parameters
        ----------

        guild_id : int

        Returns
        -------

        guild_commands : List[ApplicationCommand]
        """
        data = await self.client.http.request(
            Route(
                "GET",
                "/applications/{application_id}/guilds/{guild_id}/commands",
                application_id=self.application_id,
                guild_id=guild_id,
            )
        )
        return [application_command_factory(dat) for dat in data]

    async def fetch_global_command(self, command_id: int):
        """
        Requests a registered global command

        Parameters
        ----------

        command_id : int

        Returns
        -------

        global_command : ApplicationCommand
        """
        data = await self.client.http.request(
            Route(
                "GET",
                "/applications/{application_id}/commands/{cmd_id}",
                application_id=self.application_id,
                cmd_id=command_id,
            )
        )
        return application_command_factory(data)

    async def fetch_guild_command(self, guild_id: int, command_id: int):
        """
        Requests a registered guild command

        Parameters
        ----------

        guild_id : int

        command_id : int

        Returns
        -------

        guild_command : ApplicationCommand
        """
        data = await self.client.http.request(
            Route(
                "GET",
                "/applications/{application_id}/guilds/{guild_id}/commands/{cmd_id}",
                application_id=self.application_id,
                guild_id=guild_id,
                cmd_id=command_id,
            )
        )
        return application_command_factory(data)

    async def register_global_command(self, app_command: ApplicationCommand):
        """
        Registers a global application command

        Parameters
        ----------

        app_command : ApplicationCommand
        """
        if not isinstance(app_command, ApplicationCommand):
            raise discord.InvalidArgument("Expected an ApplicationCommand instance")
        r = await self.client.http.request(
            Route("POST", "/applications/{application_id}/commands", application_id=self.application_id),
            json=app_command.to_dict(),
        )
        sc = application_command_factory(r)
        self._global_commands[sc.id] = sc
        return sc

    async def register_guild_command(self, guild_id: int, app_command: ApplicationCommand):
        """
        Registers a local application command

        Parameters
        ----------

        guild_id : :class:`int`

        app_command : :class:`ApplicationCommand`
        """
        if not isinstance(app_command, ApplicationCommand):
            raise discord.InvalidArgument("Expected a ApplicationCommand instance")
        r = await self.client.http.request(
            Route(
                "POST",
                "/applications/{app_id}/guilds/{guild_id}/commands",
                app_id=self.application_id,
                guild_id=guild_id,
            ),
            json=app_command.to_dict(),
        )
        # Update cache
        sc = application_command_factory(r)
        self._add_guild_command(guild_id, sc)
        return sc

    async def overwrite_global_commands(self, app_commands: list):
        """
        Bulk overwrites all global application commands

        Parameters
        ----------

        app_commands : List[ApplicationCommand]
        """

        if not all(isinstance(sc, ApplicationCommand) for sc in app_commands):
            raise discord.InvalidArgument("app_commands must contain only ApplicationCommand instances")
        await self.client.http.request(
            Route("PUT", "/applications/{app_id}/commands", app_id=self.application_id),
            json=[sc.to_dict() for sc in app_commands],
        )
        # Update cache
        new_commands = await self.fetch_global_commands()
        self._global_commands = {cmd.id: cmd for cmd in new_commands}
        return new_commands

    async def overwrite_guild_commands(self, guild_id: int, app_commands: List[ApplicationCommand]):
        """
        Bulk overwrites all guild application commands

        Parameters
        ----------

        guild_id : int

        app_commands : List[ApplicationCommand]
        """
        if not all(isinstance(sc, ApplicationCommand) for sc in app_commands):
            raise discord.InvalidArgument("app_commands must contain only ApplicationCommand instances")
        await self.client.http.request(
            Route(
                "PUT",
                "/applications/{app_id}/guilds/{guild_id}/commands",
                app_id=self.application_id,
                guild_id=guild_id,
            ),
            json=[sc.to_dict() for sc in app_commands],
        )
        # Update cache
        new_commands = await self.fetch_guild_commands(guild_id)
        self._guild_commands[guild_id] = {cmd.id: cmd for cmd in new_commands}

    async def edit_global_command(self, command_id: int, app_command: ApplicationCommand, **kwargs):
        """
        Edits a global application command

        Parameters
        ----------
        command_id : int
        app_command : ApplicationCommand
            replacement of the old data
        """
        if not isinstance(app_command, ApplicationCommand):
            raise discord.InvalidArgument("parameter app_command must be ApplicationCommand")
        ignore_name = kwargs.get("ignore_name", False)
        r = await self.client.http.request(
            Route("PATCH", "/applications/{app_id}/commands/{cmd_id}", app_id=self.application_id, cmd_id=command_id),
            json=app_command.to_dict(hide_name=ignore_name),
        )
        # Update cache
        sc = application_command_factory(r)
        self._global_commands[sc.id] = sc
        return sc

    async def edit_guild_command(self, guild_id: int, command_id: int, app_command: ApplicationCommand, **kwargs):
        """
        Edits the local application command

        Parameters
        ----------
        guild_id : int
        command_id : int
        app_command : ApplicationCommand
            replacement of the old data
        """
        if not isinstance(app_command, ApplicationCommand):
            raise discord.InvalidArgument("parameter app_command must be ApplicationCommand")
        ignore_name = kwargs.get("ignore_name", False)
        r = await self.client.http.request(
            Route(
                "PATCH",
                "/applications/{app_id}/guilds/{guild_id}/commands/{cmd_id}",
                app_id=self.application_id,
                guild_id=guild_id,
                cmd_id=command_id,
            ),
            json=app_command.to_dict(hide_name=ignore_name),
        )
        # Update cache
        sc = application_command_factory(r)
        self._add_guild_command(guild_id, sc)
        return sc

    async def delete_global_command(self, command_id: int):
        """
        Deletes the global application command

        Parameters
        ----------
        command_id : int
        """
        await self.client.http.request(
            Route("DELETE", "/applications/{app_id}/commands/{cmd_id}", app_id=self.application_id, cmd_id=command_id)
        )
        # Update cache
        self._remove_global_command(command_id)

    async def delete_guild_command(self, guild_id: int, command_id: int):
        """
        Deletes the local application command

        Parameters
        ----------
        guild_id : int
        command_id : int
        """
        await self.client.http.request(
            Route(
                "DELETE",
                "/applications/{app_id}/guilds/{guild_id}/commands/{cmd_id}",
                app_id=self.application_id,
                guild_id=guild_id,
                cmd_id=command_id,
            )
        )
        # Update cache
        self._remove_guild_command(guild_id, command_id)

    async def delete_global_commands(self):
        """
        Deletes all global commands.
        """
        await self.overwrite_global_commands([])
        self._global_commands = {}

    async def delete_guild_commands(self, guild_id: int):
        """
        Deletes all local commands in the specified guild.

        Parameters
        ----------
        guild_id : int
            the ID of the guild where you're going to delete the commands
        """
        await self.overwrite_guild_commands(guild_id, [])
        if guild_id in self._guild_commands:
            del self._guild_commands[guild_id]

    # Permissions
    async def fetch_guild_command_permissions(self, guild_id: int, command_id: int):
        """
        Fetches command permissions for a specific command in a guild.

        Parameters
        ----------
        guild_id : :class:`int`
            the ID of the guild
        command_id : :class:`int`
            the ID of the command
        """
        r = await self.client.http.request(
            Route(
                "GET",
                "/applications/{app_id}/guilds/{guild_id}/commands/{command_id}/permissions",
                app_id=self.application_id,
                guild_id=guild_id,
                command_id=command_id,
            )
        )
        return ApplicationCommandPermissions.from_dict(r)

    async def batch_fetch_guild_command_permissions(self, guild_id: int):
        """
        Fetches command permissions for all commands in a guild.

        Parameters
        ----------
        guild_id : :class:`int`
            the ID of the guild
        """
        array = await self.client.http.request(
            Route(
                "GET",
                "/applications/{app_id}/guilds/{guild_id}/commands/permissions",
                app_id=self.application_id,
                guild_id=guild_id,
            )
        )
        return {int(obj["id"]): ApplicationCommandPermissions.from_dict(obj) for obj in array}

    async def edit_guild_command_permissions(
        self, guild_id: int, command_id: int, permissions: ApplicationCommandPermissions
    ):
        """
        Edits command permissions for a specific command in a guild.

        Parameters
        ----------
        guild_id : :class:`int`
            the ID of the guild
        command_id : :class:`int`
            the ID of the command
        permissions : :class:`SlashCommandPermissions` | :class:`dict`
            new permissions to set. If you use :class:`SlashCommandPermissions.from_pairs`,
            you can pass the arg of that method straight into this function
        """

        if isinstance(permissions, dict):
            permissions = ApplicationCommandPermissions.from_pairs(permissions)

        await self.client.http.request(
            Route(
                "PUT",
                "/applications/{app_id}/guilds/{guild_id}/commands/{command_id}/permissions",
                app_id=self.application_id,
                guild_id=guild_id,
                command_id=command_id,
            ),
            json=permissions.to_dict(),
        )
        # Update cache
        self._set_permissions(guild_id, command_id, permissions)

    async def batch_edit_guild_command_permissions(
        self, guild_id: int, permissions: Dict[int, ApplicationCommandPermissions]
    ):
        """
        Batch edits permissions for all commands in a guild.

        Parameters
        ----------
        guild_id : :class:`int`
            the ID of the guild
        permissions : Dict[:class:`int`, :class:`ApplicationCommandPermissions`]
            a dictionary of command IDs and permissions
        """
        data = []
        for cmd_id, perms in permissions.items():
            # Cache
            self._set_permissions(guild_id, cmd_id, perms)
            # To dict
            thing = {**perms.to_dict(), "id": cmd_id}
            data.append(thing)
        await self.client.http.request(
            Route(
                "PUT",
                "/applications/{app_id}/guilds/{guild_id}/commands/permissions",
                app_id=self.application_id,
                guild_id=guild_id,
            ),
            json=data,
        )

    # Even slower API methods
    async def fetch_global_command_named(self, name: str) -> Optional[ApplicationCommand]:
        """
        Fetches a global command that matches the specified name

        Parameters
        ----------

        name : str
            the name of the command to fetch
        """
        cmds = await self.fetch_global_commands()
        for c in cmds:
            if c.name == name:
                return c

    async def fetch_guild_command_named(self, guild_id: int, name: str):
        """
        Fetches a guild command that matches the specified name

        Parameters
        ----------

        guild_id : int
            ID of the guild where the command is registered

        name : str
            the name of the command to fetch
        """
        cmds = await self.fetch_guild_commands(guild_id)
        for cmd in cmds:
            if cmd.name == name:
                return cmd

    async def edit_global_command_named(self, name: str, app_command: ApplicationCommand):
        """
        Edits a global command matching the specified name.

        Parameters
        ----------
        name : str
            the name of the command to edit
        app_command : ApplicationCommand
            replacement of the old data
        """
        cmd = self.get_global_command_named(name)
        if cmd is not None:
            await self.edit_global_command(cmd.id, app_command)

    async def edit_guild_command_named(self, guild_id: int, name: str, app_command: ApplicationCommand):
        """
        Edits a local command matching the specified name.

        Parameters
        ----------
        guild_id : int
            ID of the guild where the command is registered
        name : str
            the name of the command to edit
        app_command : ApplicationCommand
            replacement of the old data
        """
        cmd = self.get_guild_command_named(guild_id, name)
        if cmd is not None:
            await self.edit_guild_command(guild_id, cmd.id, app_command)

    async def delete_global_command_named(self, name: str):
        """
        Deletes a global command matching the specified name.

        Parameters
        ----------
        name : str
            the name of the command to delete
        """
        cmd = self.get_global_command_named(name)
        if cmd is not None:
            await self.delete_global_command(cmd.id)

    async def delete_guild_command_named(self, guild_id: int, name: str):
        """
        Deletes a local command matching the specified name.

        Parameters
        ----------
        guild_id : int
            ID of the guild where the command is registered
        name : str
            the name of the command to edit
        """
        cmd = self.get_guild_command_named(guild_id, name)
        if cmd is not None:
            await self.delete_guild_command(guild_id, cmd.id)

    # Internal things
    def dispatch(self, event_name: str, *args, **kwargs):
        self.client.loop.create_task(self._activate_event(event_name, *args, **kwargs))

    def _add_global_command(self, command: ApplicationCommand):
        self._global_commands[command.id] = command

    def _add_guild_command(self, guild_id: int, command: ApplicationCommand):
        if guild_id not in self._guild_commands:
            self._guild_commands[guild_id] = {command.id: command}
        else:
            self._guild_commands[guild_id][command.id] = command

    def _remove_global_command(self, command_id: int):
        if command_id in self._global_commands:
            del self._global_commands[command_id]

    def _remove_guild_command(self, guild_id: int, command_id: int):
        if guild_id in self._guild_commands:
            granula = self._guild_commands[guild_id]
            if command_id in granula:
                del granula[command_id]

    def _set_permissions(self, guild_id: int, command_id: int, permissions: ApplicationCommandPermissions):
        if guild_id in self._guild_commands:
            granula = self._guild_commands[guild_id]
            if command_id in granula:
                command = granula[command_id]
                if isinstance(command, SlashCommand):
                    command.permissions = permissions

    def _error_handler_exists(self, handler_name: str) -> bool:
        cog_names = self._cogs_with_err_listeners.get(handler_name, [])
        return not (
            len(cog_names) == 0
            and not hasattr(self.client, handler_name)
            and handler_name not in self.client._listeners
            and handler_name not in self._listeners
            and handler_name not in self.events
        )

    def _inject_cogs(self, cog: Any):
        # Insert the cog into slash commands:
        if not hasattr(cog, "slash_commands"):
            cog.slash_commands = []
        for cmd in self.slash_commands.values():
            if cmd._cog_class_name == cog.__class__.__name__:
                cmd._inject_cog(cog)
                cog.slash_commands.append(cmd)
        # Insert the cog into user commands:
        if not hasattr(cog, "user_commands"):
            cog.user_commands = []
        for cmd in self.user_commands.values():
            if cmd._cog_class_name == cog.__class__.__name__:
                cmd._inject_cog(cog)
                cog.user_commands.append(cmd)
        # Insert the cog into message commands:
        if not hasattr(cog, "message_commands"):
            cog.message_commands = []
        for cmd in self.message_commands.values():
            if cmd._cog_class_name == cog.__class__.__name__:
                cmd._inject_cog(cog)
                cog.message_commands.append(cmd)
        # Auto register the commands again
        if self.is_ready:
            self.client.loop.create_task(self._auto_register_or_patch())
        # We need to know which cogs are able to dispatch errors
        pairs = cog.get_listeners()
        for event_name, func in pairs:
            cog_names = self._cogs_with_err_listeners.get(event_name)
            if cog_names is not None:
                cog_names.append(cog.qualified_name)

    def _eject_cogs(self, name: str):
        for cog_names in self._cogs_with_err_listeners.values():
            try:
                cog_names.remove(name)
            except Exception:
                pass
        # Remove the commands from cache
        bad_keys = [kw for kw, cmd in _HANDLER.slash_commands.items() if cmd._cog_name == name]
        for key in bad_keys:
            del _HANDLER.slash_commands[key]
        bad_keys = [kw for kw, cmd in _HANDLER.user_commands.items() if cmd._cog_name == name]
        for key in bad_keys:
            del _HANDLER.user_commands[key]
        bad_keys = [kw for kw, cmd in _HANDLER.message_commands.items() if cmd._cog_name == name]
        for key in bad_keys:
            del _HANDLER.message_commands[key]

    def _guilds_with_commands(self) -> List[int]:
        guilds = set()
        for cmd in _HANDLER.slash_commands.values():
            guild_ids = cmd.guild_ids or self._test_guilds
            if guild_ids is not None:
                guilds = guilds.union(set(guild_ids))
        return list(guilds)

    def _per_guild_commands(self) -> Tuple[List[SlashCommand], Dict[int, List[SlashCommand]]]:
        global_cmds = []
        guilds = {}
        for cmd in self.commands.values():
            if not cmd.auto_sync:
                continue
            guild_ids = cmd.guild_ids or self._test_guilds
            if guild_ids is None:
                global_cmds.append(cmd.registerable)
            else:
                for guild_id in guild_ids:
                    if guild_id not in guilds:
                        guilds[guild_id] = [cmd.registerable]
                    else:
                        guilds[guild_id].append(cmd.registerable)
        return global_cmds, guilds

    def _modify_parser(self, parsers: Dict[str, Callable[..., Any]], event: str, func: Callable[[Any], Any]):
        def empty_func(data):
            pass

        old_func: Callable = parsers.get(event, empty_func)
        original_func = getattr(old_func, "__original_parser__", old_func)

        def new_func(data):
            func(data)
            return original_func(data)

        new_func.__original_parser__ = original_func
        parsers[event] = new_func

    # Automatically register commands
    async def _auto_register_or_patch(self):
        """
        Assuming that all commands are already cached
        ---------------------------------------------
        """
        if not self._sync_commands:
            return
        # Sort all invokable commands between guild IDs
        global_cmds, guild_cmds = self._per_guild_commands()
        # This is for the event
        global_commands_patched = False
        patched_guilds = []
        # Update global commands first
        update_required = False
        deletion_required = False
        for cmd in global_cmds:
            old_cmd = self.get_global_command_named(cmd.name)
            if old_cmd is None or old_cmd.type == cmd.type and cmd != old_cmd:
                update_required = True
                break
            elif old_cmd.type != cmd.type:
                update_required = True
                deletion_required = True
                break
        if update_required or len(global_cmds) != len(self._global_commands):
            try:
                if deletion_required:
                    await self.delete_global_commands()
                await self.overwrite_global_commands(global_cmds)
                global_commands_patched = True
            except Exception as e:
                if self._show_warnings:
                    print(f"[WARNING] Failed to overwrite global commands due to {e}")
        # Update guild commands
        for guild_id, cmds in guild_cmds.items():
            update_required = False
            deletion_required = False
            for cmd in cmds:
                old_cmd = self.get_guild_command_named(guild_id, cmd.name)
                if old_cmd is None or old_cmd.type == cmd.type and cmd != old_cmd:
                    update_required = True
                    break
                elif old_cmd.type != cmd.type:
                    update_required = True
                    deletion_required = True
                    break
            if update_required or len(cmds) != len(self.get_guild_commands(guild_id)):
                try:
                    if deletion_required:
                        await self.delete_guild_commands(guild_id)
                    await self.overwrite_guild_commands(guild_id, cmds)  # type: ignore
                    patched_guilds.append(guild_id)
                except Exception as e:
                    if self._show_warnings:
                        print(f"[WARNING] Failed to overwrite commands in <Guild id={guild_id}> due to {e}")
        # Dispatch an event
        self.dispatch("auto_register", global_commands_patched, patched_guilds)

    async def _maybe_unregister_commands(self, guild_id: Optional[int]):
        """
        Unregisters unknown commands from the guild, if possible.
        Mainly called if a guild command isn't in the code, but
        it still exists in discord and creates interactions.
        """
        if guild_id is None:
            return

        app_commands = await self.fetch_guild_commands(guild_id)
        local_app_commands = self.get_guild_commands(guild_id)
        good_commands = [cmd for cmd in app_commands if cmd.name in local_app_commands]
        try:
            await self.overwrite_guild_commands(guild_id, good_commands)
        except Exception:
            pass

    # Cache commands
    async def _cache_global_commands(self):
        commands = await self.fetch_global_commands()
        self._global_commands = {cmd.id: cmd for cmd in commands}

    async def _cache_guild_commands(self):
        for guild_id in self._guilds_with_commands():
            try:
                commands = await self.fetch_guild_commands(guild_id)
                perms = await self.batch_fetch_guild_command_permissions(guild_id)
                if len(commands) > 0:
                    # Merge commands and permissions
                    merged_commands = {}
                    for cmd in commands:
                        if isinstance(cmd, SlashCommand) and cmd.id in perms:
                            cmd.permissions = perms[cmd.id]
                        merged_commands[cmd.id] = cmd
                    # Put to the dict
                    self._guild_commands[guild_id] = merged_commands
            except Exception:
                pass

    # Special waiter
    async def wait_for_button_click(self, check: Callable[..., bool] = None, timeout: float = None):
        if check is None:
            check = lambda ctx: True
        future = self.client.loop.create_future()
        if "button_click" not in self._listeners:
            self._listeners["button_click"] = []
        listeners = self._listeners["button_click"]
        listeners.append((future, check))
        return await asyncio.wait_for(future, timeout)

    async def wait_for_dropdown(self, check: Callable[..., bool] = None, timeout: float = None):
        if check is None:
            check = lambda ctx: True
        future = self.client.loop.create_future()
        if "dropdown" not in self._listeners:
            self._listeners["dropdown"] = []
        listeners = self._listeners["dropdown"]
        listeners.append((future, check))
        return await asyncio.wait_for(future, timeout)

    async def multiple_wait_for(self, events_and_checks: Dict[str, Any], timeout: float = None):
        """
        Waits until one of the given events toggles and matches the relevant check.

        Example:

        ::

            result = None
            try:
                result = await client.multiple_wait_for(
                    {
                        "message": lambda msg: msg.author == ctx.author,
                        "reaction_add": lambda react, user: user == ctx.author
                    },
                    timeout=60
                )
            except asyncio.TimeoutError:
                await ctx.send("It took too long")
            if isinstance(result, discord.Message):
                # on_message was toggled
                await ctx.send(f"You said '{result.content}'")
            else:
                # on_reaction_add was toggled
                reaction, user = result
                await ctx.send(f"Your reaction: {reaction.emoji}")

        Parameters
        ----------
        events_and_checks : Dict[:class:`str`, :class:`function | None`]
            a dictionary of event names and relevant checks, e.g.
            ``{"message": lambda m: m.author == ctx.author, "button_click": None}``
        timeout : :class:`float` | :class:`None`
            the amount of seconds the bot should wait for any of the given events
        """

        coros_and_events = {}
        waiters = []
        for event, check in events_and_checks.items():
            coro = self.client.wait_for(event, check=check, timeout=timeout)
            coros_and_events[id(coro)] = event
            waiters.append(coro)
        # Wait for some of the waiters to toggle
        done, pending = await asyncio.wait(waiters, return_when=asyncio.FIRST_COMPLETED)
        # Get the result or catch an exception
        try:
            stuff = done.pop().result()
            err = None
        except Exception as error:
            stuff = None
            err = error
        # Clean other waiters
        for future in done:
            future.exception()
        for future in pending:
            future.cancel()
        # Error or result
        if err is not None:
            raise err
        return stuff

    # Adding relevant listeners
    def _on_raw_interaction(self, data: Dict[str, Any]):
        self.client.loop.create_task(self._process_interaction(data))

    async def _on_socket_response(self, payload: Dict[str, Any]):
        if payload.get("t") != "INTERACTION_CREATE":
            return
        await self._process_interaction(payload["d"])

    async def _on_shard_connect(self, shard_id: int):
        self.active_shard_count += 1
        if self.active_shard_count == 1:
            await self._fill_app_id()
            await self._cache_global_commands()
            await self._cache_guild_commands()
            await self._auto_register_or_patch()
        if self._uses_discord_2:
            self._modify_parser(
                self.client._AutoShardedClient__shards[shard_id].ws._discord_parsers,
                "INTERACTION_CREATE",
                self._on_raw_interaction,
            )

    async def _on_connect(self):
        if not isinstance(self.client, discord.AutoShardedClient):
            if self._uses_discord_2:
                self._modify_parser(self.client.ws._discord_parsers, "INTERACTION_CREATE", self._on_raw_interaction)
            await self._fill_app_id()
            await self._cache_global_commands()
            await self._cache_guild_commands()
            await self._auto_register_or_patch()
            self.is_ready = True
            await self._activate_event("ready")

    async def _on_ready(self):
        if isinstance(self.client, discord.AutoShardedClient):
            self.is_ready = True
            await self._activate_event("ready")

    async def _on_guild_remove(self, guild: Guild):
        if guild.id in self._guild_commands:
            del self._guild_commands[guild.id]

    async def _on_slash_command(self, inter: SlashInteraction):
        app_command = self.slash_commands.get(inter.data.name)
        if app_command is None:
            await self._maybe_unregister_commands(inter.guild_id)
            return
        else:
            guild_ids = app_command.guild_ids or self._test_guilds
            is_global = self.get_global_command(inter.data.id) is not None
            if guild_ids is None:
                usable = is_global
            else:
                usable = not is_global and inter.guild_id in guild_ids
        if usable:
            try:
                await app_command.invoke(inter)
            except Exception as err:
                if self._error_handler_exists("on_slash_command_error"):
                    await self._activate_event("slash_command_error", inter, err)
                elif app_command._error_handler is None:
                    raise err
        else:
            await self._maybe_unregister_commands(inter.guild_id)

    async def _on_user_command(self, inter: ContextMenuInteraction):
        app_command = _HANDLER.user_commands.get(inter.data.name)
        if app_command is None:
            await self._maybe_unregister_commands(inter.guild_id)
            return
        else:
            guild_ids = app_command.guild_ids or self._test_guilds
            is_global = self.get_global_command(inter.data.id) is not None
            if guild_ids is None:
                usable = is_global
            else:
                usable = not is_global and inter.guild_id in guild_ids
        if usable:
            try:
                await app_command.invoke(inter)
            except Exception as err:
                if self._error_handler_exists("on_user_command_error"):
                    await self._activate_event("user_command_error", inter, err)
                elif app_command._error_handler is None:
                    raise err
        else:
            await self._maybe_unregister_commands(inter.guild_id)

    async def _on_message_command(self, inter: ContextMenuInteraction):
        app_command = _HANDLER.message_commands.get(inter.data.name)
        if app_command is None:
            await self._maybe_unregister_commands(inter.guild_id)
            return
        else:
            guild_ids = app_command.guild_ids or self._test_guilds
            is_global = self.get_global_command(inter.data.id) is not None
            if guild_ids is None:
                usable = is_global
            else:
                usable = not is_global and inter.guild_id in guild_ids
        if usable:
            try:
                await app_command.invoke(inter)
            except Exception as err:
                if self._error_handler_exists("on_message_command_error"):
                    await self._activate_event("message_command_error", inter, err)
                elif app_command._error_handler is None:
                    raise err
        else:
            await self._maybe_unregister_commands(inter.guild_id)

    async def _toggle_listeners(self, event: str, *args, **kwargs):
        listeners = self._listeners.get(event)
        if listeners:
            removed = []
            for i, (future, condition) in enumerate(listeners):
                if future.cancelled():
                    removed.append(i)
                    continue

                try:
                    result = condition(*args)
                except Exception as exc:
                    future.set_exception(exc)
                    removed.append(i)
                else:
                    if result:
                        if len(args) == 0:
                            future.set_result(None)
                        elif len(args) == 1:
                            future.set_result(args[0])
                        else:
                            future.set_result(args)
                        removed.append(i)
            if len(removed) == len(listeners):
                self._listeners.pop(event)
            else:
                for idx in reversed(removed):
                    del listeners[idx]

    async def _activate_event(self, event_name: str, *args, **kwargs):
        await self._toggle_listeners(event_name, *args, **kwargs)
        if event_name != "ready":
            self.client.dispatch(event_name, *args, **kwargs)
        func = self.events.get(event_name)
        if func:
            await func(*args, **kwargs)

    async def _process_interaction(self, payload: Dict[str, Any]):
        event_name = "dislash_interaction" if self._uses_discord_2 else "interaction"
        _type = payload.get("type", 1)
        # Received a ping
        if _type == 1:
            inter = BaseInteraction(self.client, payload)
            self.dispatch(event_name, inter)
            await inter.create_response(type=1)
        # Application command invoked
        elif _type == 2:
            data_type = payload.get("data", {}).get("type", 1)
            if data_type == 1:
                inter = SlashInteraction(self.client, payload)
                self.dispatch(event_name, inter)
                self.dispatch("slash_command", inter)
                await self._on_slash_command(inter)
            elif data_type in (2, 3):
                inter = ContextMenuInteraction(self.client, payload)
                self.dispatch(event_name, inter)
                if data_type == 2:
                    self.dispatch("user_command", inter)
                    await self._on_user_command(inter)
                elif data_type == 3:
                    self.dispatch("message_command", inter)
                    await self._on_message_command(inter)
        # Message component clicked
        elif _type == 3:
            inter = MessageInteraction(self.client, payload)
            self.dispatch(event_name, inter)
            self.dispatch("message_interaction", inter)
            if inter.component is None:
                return
            if inter.component.type == ComponentType.Button:
                self.dispatch("button_click", inter)
            elif inter.component.type == ComponentType.SelectMenu:
                self.dispatch("dropdown", inter)

    async def _fill_app_id(self):
        data = await self.client.http.application_info()
        self.application_id = int(data["id"])

    command = slash_command


SlashClient = InteractionClient
