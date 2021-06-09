from discord.abc import Messageable
from discord.http import Route
from discord.ext.commands import Context
import asyncio
import discord

from .slash_core import SlashCommandResponse, get_class
from .slash_command import SlashCommand, SlashCommandPermissions
from .utils import ClickListener, _on_button_click
from ._decohub import _HANDLER
from ._send_modifications import *

from ..interactions import ComponentType, SlashInteraction, MessageInteraction


__all__ = ("SlashClient",)


class SlashClient:
    """
    The main purpose of this class is to track ``INTERACTION_CREATE`` API event.

    Parameters
    ----------
    client : :class:`commands.Bot` | :class:`commands.AutoShardedBot`
        The discord.py Bot instance
    show_warnings : :class:`bool`
        Whether to show the warnings or not
    modify_send : :class:`bool`
        Whether to modify :class:`Messageable.send` and :class:`Message.edit`.
        Modified methods allow to specify the ``components`` parameter.

    Attributes
    ----------
    client : :class:`commands.Bot` | :class:`commands.AutoShardedBot`
    global_commands : :class:`list`
        All registered global commands are cached here
    commands : :class:`list`
        All working slash commands
    is_ready : bool
        Equals to ``True`` if SlashClient is ready, otherwise it's ``False``
    """
    def __init__(self, client, *, show_warnings: bool=False, modify_send: bool=True):
        _HANDLER.client = client
        self.client = _HANDLER.client
        self.events = {}
        self._listeners = {}
        self._global_commands = {}
        self._guild_commands = {}
        self._show_warnings = show_warnings
        self._modify_send = modify_send
        self.active_shard_count = 0
        self.is_ready = False
        # Add listeners
        self._register_listeners()
        # Modify old discord.py methods
        self._modify_discord()
        # Link the slash ext to client if doesn't already exist
        if not hasattr(self.client, "slash"):
            self.client.slash = self
        # Inject cogs that are already loaded
        for cog in self.client.cogs.values():
            self._inject_cogs(cog)
    
    def _register_listeners(self):
        self.client.add_listener(self._on_guild_remove, 'on_guild_remove')
        self.client.add_listener(self._on_socket_response, 'on_socket_response')
        if isinstance(self.client, discord.AutoShardedClient):
            self.client.add_listener(self._on_shard_connect, 'on_shard_connect')
            self.client.add_listener(self._on_ready, 'on_ready')
        else:
            self.client.add_listener(self._on_connect, 'on_connect')
        # For nice click listener
        self.client.add_listener(_on_button_click, 'on_button_click')

    def _modify_discord(self):
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

        async def fetch_commands(guild):
            return await self.fetch_guild_commands(guild.id)
        
        async def fetch_command(guild, command_id):
            return await self.fetch_guild_command(guild.id, command_id)
        
        async def edit_command(guild, command_id, slash_command):
            return await self.edit_guild_slash_command(guild.id, command_id, slash_command)
        
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

        if self._modify_send:
            Messageable.send = send_with_components
            discord.Message.edit = edit_with_components
        Context.wait_for_button_click = ctx_wait_for_button_click
        discord.Message.create_click_listener = create_click_listener
        discord.Message.wait_for_button_click = message_wait_for_button_click
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

    def teardown(self):
        '''Cleanup the client by removing all registered listeners and caches.'''
        self.client.remove_listener(self._on_guild_remove, 'on_guild_remove')
        self.client.remove_listener(self._on_socket_response, 'on_socket_response')
        if isinstance(self.client, discord.AutoShardedClient):
            self.client.remove_listener(self._on_shard_connect, 'on_shard_connect')
            self.client.remove_listener(self._on_ready, 'on_ready')
        else:
            self.client.remove_listener(self._on_connect, 'on_connect')

        self.events.clear()
        self._listeners.clear()
        self._global_commands.clear()
        self._guild_commands.clear()
        if hasattr(self.client, "slash"):
            del self.client.slash
        self.is_ready = False

    @property
    def commands(self):
        return _HANDLER.commands
    
    @property
    def global_commands(self):
        return [sc for sc in self._global_commands.values()]

    def event(self, func):
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
            raise TypeError(f'<{func.__qualname__}> must be a coroutine function')
        name = func.__name__
        if name.startswith('on_'):
            name = name[3:]
            if name in [
                'slash_command', 'slash_command_error',
                'ready', 'auto_register', 'button_click'
                ]:
                self.events[name] = func
        return func

    def command(self, *args, **kwargs):
        """
        A decorator that registers a function below as response for specified slash-command.

        Parameters are similar to SlashCommand arguments.

        If ``description`` is specified, the decorator will be interpreted as SlashCommand and
        will be registered (or edited) automatically with the given set of arguments.

        Parameters
        ----------

        name : str
            name of the slash-command you want to respond to (equals to function name by default)
        description : str
            if specified, the client will automatically register a command with this description
        options : List[Option]
            if specified, the client will
            automatically register a command with this list of options. Requires ``description``
        default_permission : :class:`bool`
            whether the command is enabled by default when the app is added to a guild.
            Requires ``description``
        guild_ids : List[int]
            if specified, the client will register a command in these guilds.
            Otherwise this command will be registered globally. Requires ``description``
        """
        def decorator(func):
            if not asyncio.iscoroutinefunction(func):
                raise TypeError(f'<{func.__qualname__}> must be a coroutine function')
            name = kwargs.get('name', func.__name__)
            new_func = SlashCommandResponse(
                self.client, func, name,
                kwargs.get('description'),
                kwargs.get('options'),
                kwargs.get("default_permission", True),
                kwargs.get('guild_ids')
            )
            self.commands[name] = new_func
            return new_func
        return decorator
    
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
            if cmd.name == name:
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

        slash_commands : List[SlashCommand]
        """
        granula = self._guild_commands.get(guild_id, {})
        return [sc for sc in granula.values()]

    # Straight references to API
    async def fetch_global_commands(self):
        """
        Requests a list of global registered commands from the API

        Returns
        -------

        global_commands : List[SlashCommand]
        """
        data = await self.client.http.request(
            Route('GET', '/applications/{app_id}/commands', app_id=self.client.user.id)
        )
        return [SlashCommand.from_dict(dat) for dat in data]

    async def fetch_guild_commands(self, guild_id: int):
        """
        Requests a list of registered commands for a specific guild

        Parameters
        ----------

        guild_id : int

        Returns
        -------

        guild_commands : List[SlashCommand]
        """
        data = await self.client.http.request(
            Route('GET', '/applications/{app_id}/guilds/{guild_id}/commands',
            app_id=self.client.user.id, guild_id=guild_id)
        )
        return [SlashCommand.from_dict(dat) for dat in data]
    
    async def fetch_global_command(self, command_id: int):
        """
        Requests a registered global slash-command

        Parameters
        ----------

        command_id : int

        Returns
        -------

        global_command : SlashCommand
        """
        data = await self.client.http.request(
            Route(
                "GET",
                "/applications/{app_id}/commands/{cmd_id}",
                app_id=self.client.user.id,
                cmd_id=command_id
            )
        )
        return SlashCommand.from_dict(data)

    async def fetch_guild_command(self, guild_id: int, command_id: int):
        """
        Requests a registered guild command

        Parameters
        ----------

        guild_id : int

        command_id : int

        Returns
        -------

        guild_command : SlashCommand
        """
        data = await self.client.http.request(
            Route(
                "GET",
                "/applications/{app_id}/guilds/{guild_id}/commands/{cmd_id}",
                app_id=self.client.user.id,
                guild_id=guild_id,
                cmd_id=command_id
            )
        )
        return SlashCommand.from_dict(data)

    async def register_global_slash_command(self, slash_command: SlashCommand):
        """
        Registers a global slash-command

        .. seealso:: :ref:`raw_slash_command`
        
        Parameters
        ----------

        slash_command : SlashCommand
        """
        if not isinstance(slash_command, SlashCommand):
            raise ValueError('Expected a <SlashCommand> instance')
        r = await self.client.http.request(
            Route(
                "POST",
                "/applications/{app_id}/commands",
                app_id=self.client.user.id
            ),
            json=slash_command.to_dict()
        )
        sc = SlashCommand.from_dict(r)
        self._global_commands[sc.id] = sc
        return sc
    
    async def register_guild_slash_command(self, guild_id: int, slash_command: SlashCommand):
        """
        Registers a local slash-command
        
        .. seealso:: :ref:`raw_slash_command`
        
        Parameters
        ----------

        guild_id : int

        slash_command : SlashCommand
        """
        if not isinstance(slash_command, SlashCommand):
            raise discord.InvalidArgument('Expected a <SlashCommand> instance')
        r = await self.client.http.request(
            Route(
                "POST",
                "/applications/{app_id}/guilds/{guild_id}/commands",
                app_id=self.client.user.id,
                guild_id=guild_id
            ),
            json=slash_command.to_dict()
        )
        # Update cache
        sc = SlashCommand.from_dict(r)
        self._add_guild_command(guild_id, sc)
        return sc
    
    async def overwrite_global_commands(self, slash_commands: list):
        """
        Bulk overwrites all global commands
        
        Parameters
        ----------

        slash_commands : List[SlashCommand]
        """

        if not all(isinstance(sc, SlashCommand) for sc in slash_commands):
            raise discord.InvalidArgument("slash_commands must contain only SlashCommand instances")
        await self.client.http.request(
            Route(
                "PUT",
                "/applications/{app_id}/commands",
                app_id=self.client.user.id
            ),
            json=[sc.to_dict() for sc in slash_commands]
        )
        # Update cache
        new_commands = await self.fetch_global_commands()
        self._global_commands = {cmd.id: cmd for cmd in new_commands}
        return new_commands

    async def overwrite_guild_commands(self, guild_id: int, slash_commands: list):
        """
        Bulk overwrites all guild commands
        
        Parameters
        ----------

        guild_id : int

        slash_commands : List[SlashCommand]
        """
        if not all(isinstance(sc, SlashCommand) for sc in slash_commands):
            raise discord.InvalidArgument("slash_commands must contain only SlashCommand instances")
        await self.client.http.request(
            Route(
                "PUT",
                "/applications/{app_id}/guilds/{guild_id}/commands",
                app_id=self.client.user.id,
                guild_id=guild_id
            ),
            json=[sc.to_dict() for sc in slash_commands]
        )
        # Update cache
        new_commands = await self.fetch_guild_commands(guild_id)
        self._guild_commands[guild_id] = {cmd.id: cmd for cmd in new_commands}

    async def edit_global_slash_command(self, command_id: int, slash_command: SlashCommand, **kwargs):
        """
        Edits a global command

        Parameters
        ----------
        command_id : int
        slash_command : SlashCommand
            replacement of the old data
        """
        if not isinstance(slash_command, SlashCommand):
            raise discord.InvalidArgument('parameter slash_command must be SlashCommand')
        ignore_name = kwargs.get("ignore_name", False)
        r = await self.client.http.request(
            Route(
                "PATCH",
                "/applications/{app_id}/commands/{cmd_id}",
                app_id=self.client.user.id,
                cmd_id=command_id
            ),
            json=slash_command.to_dict(hide_name=ignore_name)
        )
        # Update cache
        sc = SlashCommand.from_dict(r)
        self._global_commands[sc.id] = sc
        return sc
    
    async def edit_guild_slash_command(self, guild_id: int, command_id: int, slash_command: SlashCommand, **kwargs):
        """
        Edits a local command

        Parameters
        ----------
        guild_id : int
        command_id : int
        slash_command : SlashCommand
            replacement of the old data
        """
        if not isinstance(slash_command, SlashCommand):
            raise discord.InvalidArgument('parameter slash_command must be SlashCommand')
        ignore_name = kwargs.get("ignore_name", False)
        r = await self.client.http.request(
            Route(
                "PATCH",
                "/applications/{app_id}/guilds/{guild_id}/commands/{cmd_id}",
                app_id=self.client.user.id,
                guild_id=guild_id,
                cmd_id=command_id
            ),
            json=slash_command.to_dict(hide_name=ignore_name)
        )
        # Update cache
        sc = SlashCommand.from_dict(r)
        self._add_guild_command(guild_id, sc)
        return sc
    
    async def delete_global_slash_command(self, command_id: int):
        """
        Deletes a global command

        Parameters
        ----------

        command_id : int
        """
        await self.client.http.request(
            Route(
                "DELETE",
                "/applications/{app_id}/commands/{cmd_id}",
                app_id=self.client.user.id,
                cmd_id=command_id
            )
        )
        # Update cache
        self._remove_global_command(command_id)
    
    async def delete_guild_slash_command(self, guild_id: int, command_id: int):
        """
        Deletes a local command

        Parameters
        ----------

        guild_id : int

        command_id : int
        """
        await self.client.http.request(
            Route(
                "DELETE",
                "/applications/{app_id}/guilds/{guild_id}/commands/{cmd_id}",
                app_id=self.client.user.id,
                guild_id=guild_id,
                cmd_id=command_id
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
                app_id=self.client.user.id,
                guild_id=guild_id,
                command_id=command_id
            )
        )
        return SlashCommandPermissions.from_dict(r)

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
                app_id=self.client.user.id,
                guild_id=guild_id
            )
        )
        return {int(obj["id"]): SlashCommandPermissions.from_dict(obj) for obj in array}

    async def edit_guild_command_permissions(self, guild_id: int, command_id: int, permissions: SlashCommandPermissions):
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
            permissions = SlashCommandPermissions.from_pairs(permissions)

        await self.client.http.request(
            Route(
                "PUT",
                "/applications/{app_id}/guilds/{guild_id}/commands/{command_id}/permissions",
                app_id=self.client.user.id,
                guild_id=guild_id,
                command_id=command_id
            ),
            json=permissions.to_dict()
        )
        # Update cache
        self._set_permissions(guild_id, command_id, permissions)
    
    async def batch_edit_guild_command_permissions(self, guild_id: int, permissions: dict):
        """
        Batch edits permissions for all commands in a guild.

        Parameters
        ----------
        guild_id : :class:`int`
            the ID of the guild
        permissions : :class:`dict`
            a dictionary of ``command_id``: :class:`SlashCommandPermissions`
        """

        data = []
        for cmd_id, perms in permissions.items():
            # Cache
            self._set_permissions(guild_id, cmd_id, perms)
            # To dict
            thing = perms.to_dict()
            thing["id"] = cmd_id
            data.append(thing)
        await self.client.http.request(
            Route(
                "PUT",
                "/applications/{app_id}/guilds/{guild_id}/commands/permissions",
                app_id=self.client.user.id,
                guild_id=guild_id
            ),
            json=data
        )

    # Even slower API methods
    async def fetch_global_command_named(self, name: str):
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

    async def edit_global_command_named(self, name: str, slash_command: SlashCommand):
        """
        Edits a global command matching the specified name.

        Parameters
        ----------

        name : str
            the name of the command to edit
        
        slash_command : SlashCommand
            replacement of the old data
        """
        cmd = self.get_global_command_named(name)
        if cmd is not None:
            await self.edit_global_command(cmd.id, slash_command)

    async def edit_guild_command_named(self, guild_id: int, name: str, slash_command: SlashCommand):
        """
        Edits a local command matching the specified name.

        Parameters
        ----------

        guild_id : int
            ID of the guild where the command is registered

        name : str
            the name of the command to edit
        
        slash_command : SlashCommand
            replacement of the old data
        """
        cmd = self.get_guild_command_named(guild_id, name)
        if cmd is not None:
            await self.edit_guild_command(guild_id, cmd.id, slash_command)

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
    def _add_global_command(self, command):
        self._global_commands[command.id] = command

    def _add_guild_command(self, guild_id, command):
        if guild_id not in self._guild_commands:
            self._guild_commands[guild_id] = {command.id: command}
        else:
            self._guild_commands[guild_id][command.id] = command

    def _remove_global_command(self, command_id):
        if command_id in self._global_commands:
            del self._global_commands[command_id]

    def _remove_guild_command(self, guild_id, command_id):
        if guild_id in self._guild_commands:
            granula = self._guild_commands[guild_id]
            if command_id in granula:
                del granula[command_id]

    def _set_permissions(self, guild_id, command_id, permissions):
        if guild_id in self._guild_commands:
            granula = self._guild_commands[guild_id]
            if command_id in granula:
                granula[command_id].permissions = permissions

    def _inject_cogs(self, cog):
        for cmd in self.commands.values():
            if cmd._cog_class_name == cog.__class__.__name__:
                cmd._inject_cog(cog)
        if self.is_ready:
            self.client.loop.create_task(self._auto_register_or_patch())
    
    def _eject_cogs(self, name):
        bad_keys = []
        for kw, cmd in _HANDLER.commands.items():
            if cmd._cog_name == name:
                bad_keys.append(kw)
        for key in bad_keys:
            del _HANDLER.commands[key]

    def _guilds_with_commands(self):
        guilds = set()
        for cmd in _HANDLER.commands.values():
            if cmd.guild_ids is not None:
                guilds = guilds.union(set(cmd.guild_ids))
        return list(guilds)

    def _per_guild_commands(self):
        global_cmds = []
        guilds = {}
        for cmd in _HANDLER.commands.values():
            if cmd.guild_ids is None:
                global_cmds.append(cmd.registerable)
            else:
                for guild_id in cmd.guild_ids:
                    if guild_id not in guilds:
                        guilds[guild_id] = [cmd.registerable]
                    else:
                        guilds[guild_id].append(cmd.registerable)
        return global_cmds, guilds

    # Automatically register commands
    async def _auto_register_or_patch(self):
        """
        Assuming that all commands are already cached
        ---------------------------------------------
        """
        global_cmds, guild_cmds = self._per_guild_commands()
        total_posts = 0
        # Update global commands first
        update_required = False
        if len(global_cmds) != len(self._global_commands):
            update_required = True
        else:
            for cmd in global_cmds:
                old_cmd = self.get_global_command_named(cmd.name)
                if old_cmd is None or not cmd == old_cmd:
                    update_required = True
                    break
        if update_required:
            try:
                await self.overwrite_global_commands(global_cmds)
                total_posts += 1
            except Exception as e:
                if self._show_warnings:
                    print(f"[WARNING] Failed to overwrite global commands due to {e}")
        # Update guild commands
        for guild_id, cmds in guild_cmds.items():
            update_required = False
            if len(cmds) != len(self.get_guild_commands(guild_id)):
                update_required = True
            else:
                for cmd in cmds:
                    old_cmd = self.get_guild_command_named(guild_id, cmd.name)
                    if old_cmd is None or not (cmd == old_cmd):
                        update_required = True
                        break
            if update_required:
                try:
                    await self.overwrite_guild_commands(guild_id, cmds)
                    total_posts += 1
                except Exception as e:
                    if self._show_warnings:
                        print(f"[WARNING] Failed to overwrite commands in <Guild id={guild_id}> due to {e}")
        # Dispatch an event
        if total_posts > 0:
            self.client.loop.create_task(
                self._activate_event('auto_register', total_posts, 0)
            )

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
                        if cmd.id in perms:
                            cmd.permissions = perms[cmd.id]
                        merged_commands[cmd.id] = cmd
                    # Put to the dict
                    self._guild_commands[guild_id] = merged_commands
            except Exception:
                pass

    # Special waiter
    async def wait_for_button_click(self, check=None, timeout=None):
        if check is None:
            check = lambda ctx: True
        future = self.client.loop.create_future()
        if "button_click" not in self._listeners:
            self._listeners["button_click"] = []
        listeners = self._listeners["button_click"]
        listeners.append((future, check))
        return await asyncio.wait_for(future, timeout)


    # Adding relevant listeners
    async def _on_socket_response(self, payload):
        if payload.get("t") != "INTERACTION_CREATE":
            return
        await self._process_interaction(payload["d"])

    async def _on_shard_connect(self, shard_id):
        self.active_shard_count += 1
        if self.active_shard_count == 1:
            await self._cache_global_commands()
            await self._cache_guild_commands()
            await self._auto_register_or_patch()
    
    async def _on_connect(self):
        if not isinstance(self.client, discord.AutoShardedClient):
            await self._cache_global_commands()
            await self._cache_guild_commands()
            await self._auto_register_or_patch()
            self.is_ready = True
            await self._activate_event('ready')
    
    async def _on_ready(self):
        if isinstance(self.client, discord.AutoShardedClient):
            self.is_ready = True
            await self._activate_event('ready')

    async def _on_guild_remove(self, guild):
        if guild.id in self._guild_commands:
            del self._guild_commands[guild.id]

    async def _toggle_listeners(self, event, *args, **kwargs):
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
                    else:
                        # Add on_check_fail in the future
                        pass

            if len(removed) == len(listeners):
                self._listeners.pop(event)
            else:
                for idx in reversed(removed):
                    del listeners[idx]

    async def _activate_event(self, event_name, *args, **kwargs):
        await self._toggle_listeners(event_name, *args, **kwargs)
        if event_name != "ready":
            self.client.dispatch(event_name, *args, **kwargs)
        func = self.events.get(event_name)
        if func is not None:
            cog = get_class(func)
            if cog is not None:
                await func(cog(self.client), *args, **kwargs)
            else:
                await func(*args, **kwargs)

    async def _process_interaction(self, payload):
        _type = payload.get("type", 1)
        if _type == 2:
            inter = SlashInteraction(self.client, payload)
            # Activate event
            await self._activate_event('slash_command', inter)
            # Invoke command
            SCR = self.commands.get(inter.data.name)
            if SCR is not None:
                try:
                    await SCR.invoke(inter)
                except Exception as err:
                    await self._activate_event('slash_command_error', inter, err)
        elif _type == 3:
            inter = MessageInteraction(self.client, payload)
            if inter.component.type == ComponentType.Button:
                await self._activate_event('button_click', inter)
            elif inter.component.type == ComponentType.SelectMenu:
                # FIXME: naming might be different
                await self._activate_event('select_menu_click', inter)
    
    # Aliases
    register_global_command = register_global_slash_command
    
    register_guild_command = register_guild_slash_command

    edit_global_command = edit_global_slash_command

    edit_guild_command = edit_guild_slash_command

    delete_global_command = delete_global_slash_command

    delete_guild_command = delete_guild_slash_command
