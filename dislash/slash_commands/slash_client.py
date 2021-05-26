from discord.http import Route
from discord.errors import Forbidden
import asyncio
import discord

from .slash_core import SlashCommandResponse, get_class
from .slash_command import SlashCommand, SlashCommandPermissions
from ._decohub import _HANDLER

from ..interactions import Interaction


__all__ = ("SlashClient",)


class SlashClient:
    '''
    The main purpose of this class is to track ``INTERACTION_CREATE`` API event.

    Parameters
    ----------
    client : :class:`commands.Bot` | :class:`commands.AutoShardedBot`

    Attributes
    ----------
    client : :class:`commands.Bot` | :class:`commands.AutoShardedBot`
    global_commands : :class:`list`
        All registered global commands are cached here
    is_ready : bool
        Equals to ``True`` if SlashClient is ready, otherwise it's ``False``
    '''
    def __init__(self, client, *, show_warnings: bool=False):
        _HANDLER.client = client
        self.client = _HANDLER.client
        self.events = {}
        self._global_commands = {}
        self._guild_commands = {}
        self._show_warnings = show_warnings
        self.active_shard_count = 0
        self.is_ready = False
        self.client.add_listener(self._on_shard_connect, 'on_shard_connect')
        self.client.add_listener(self._on_connect, 'on_connect')
        self.client.add_listener(self._on_guild_remove, 'on_guild_remove')
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
        # Link the slash ext to client
        self.client.slash = self
        # Inject cogs that are already loaded
        for cog in self.client.cogs.values():
            self._inject_cogs(cog)
    @property
    def commands(self):
        return _HANDLER.commands
    @property
    def global_commands(self):
        return [sc for sc in self._global_commands.values()]

    def event(self, func):
        '''
        Decorator
        ::
        
            @slash.event
            async def on_ready():
                print("SlashClient is ready")
        
        | All possible events:
        | ``on_ready``, ``on_auto_register``,
        | ``on_slash_command``, ``on_slash_command_error``
        '''
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'<{func.__qualname__}> must be a coroutine function')
        name = func.__name__
        if name.startswith('on_'):
            name = name[3:]
            if name in [
                'slash_command', 'slash_command_error',
                'ready', 'auto_register'
                ]:
                self.events[name] = func
        return func

    def command(self, *args, **kwargs):
        '''
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
        '''
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
        '''Requests a list of global registered commands from the API

        Returns
        -------

        global_commands : List[SlashCommand]
        '''
        data = await self.client.http.request(
            Route('GET', '/applications/{app_id}/commands', app_id=self.client.user.id)
        )
        return [SlashCommand.from_dict(dat) for dat in data]

    async def fetch_guild_commands(self, guild_id: int):
        '''Requests a list of registered commands for a specific guild

        Parameters
        ----------

        guild_id : int

        Returns
        -------

        guild_commands : List[SlashCommand]
        '''
        data = await self.client.http.request(
            Route('GET', '/applications/{app_id}/guilds/{guild_id}/commands',
            app_id=self.client.user.id, guild_id=guild_id)
        )
        return [SlashCommand.from_dict(dat) for dat in data]
    
    async def fetch_global_command(self, command_id: int):
        '''Requests a registered global slash-command

        Parameters
        ----------

        command_id : int

        Returns
        -------

        global_command : SlashCommand
        '''
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
        '''
        Requests a registered guild command

        Parameters
        ----------

        guild_id : int

        command_id : int

        Returns
        -------

        guild_command : SlashCommand
        '''
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
        '''Registers a global slash-command

        .. seealso:: :ref:`raw_slash_command`
        
        Parameters
        ----------

        slash_command : SlashCommand
        '''
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
        '''Registers a local slash-command
        
        .. seealso:: :ref:`raw_slash_command`
        
        Parameters
        ----------

        guild_id : int

        slash_command : SlashCommand
        '''
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
        '''
        Bulk overwrites all global commands
        
        Parameters
        ----------

        slash_commands : List[SlashCommand]
        '''

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
        '''
        Bulk overwrites all guild commands
        
        Parameters
        ----------

        guild_id : int

        slash_commands : List[SlashCommand]
        '''
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
        '''
        Edits a global command

        Parameters
        ----------
        command_id : int
        slash_command : SlashCommand
            replacement of the old data
        '''
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
        '''Edits a local command

        Parameters
        ----------
        guild_id : int
        command_id : int
        slash_command : SlashCommand
            replacement of the old data
        '''
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
        '''Deletes a global command

        Parameters
        ----------

        command_id : int
        '''
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
        '''Deletes a local command

        Parameters
        ----------

        guild_id : int

        command_id : int
        '''
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
        '''
        Fetches a global command that matches the specified name

        Parameters
        ----------

        name : str
            the name of the command to fetch
        '''
        cmds = await self.fetch_global_commands()
        for c in cmds:
            if c.name == name:
                return c

    async def fetch_guild_command_named(self, guild_id: int, name: str):
        '''
        Fetches a guild command that matches the specified name

        Parameters
        ----------

        guild_id : int
            ID of the guild where the command is registered

        name : str
            the name of the command to fetch
        '''
        cmds = await self.fetch_guild_commands(guild_id)
        for cmd in cmds:
            if cmd.name == name:
                return cmd

    async def edit_global_command_named(self, name: str, slash_command: SlashCommand):
        '''
        Edits a global command matching the specified name.

        Parameters
        ----------

        name : str
            the name of the command to edit
        
        slash_command : SlashCommand
            replacement of the old data
        '''
        cmd = self.get_global_command_named(name)
        if cmd is not None:
            await self.edit_global_command(cmd.id, slash_command)

    async def edit_guild_command_named(self, guild_id: int, name: str, slash_command: SlashCommand):
        '''
        Edits a local command matching the specified name.

        Parameters
        ----------

        guild_id : int
            ID of the guild where the command is registered

        name : str
            the name of the command to edit
        
        slash_command : SlashCommand
            replacement of the old data
        '''
        cmd = self.get_guild_command_named(guild_id, name)
        if cmd is not None:
            await self.edit_guild_command(guild_id, cmd.id, slash_command)

    async def delete_global_command_named(self, name: str):
        '''
        Deletes a global command matching the specified name.

        Parameters
        ----------

        name : str
            the name of the command to delete
        '''
        cmd = self.get_global_command_named(name)
        if cmd is not None:
            await self.delete_global_command(cmd.id)

    async def delete_guild_command_named(self, guild_id: int, name: str):
        '''
        Deletes a local command matching the specified name.

        Parameters
        ----------

        guild_id : int
            ID of the guild where the command is registered

        name : str
            the name of the command to edit
        '''
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
            if cmd._cog_name == cog.__cog_name__:
                cmd._inject_cog(cog)
        if self.is_ready:
            self.client.loop.create_task(self._auto_register_or_patch())
    
    def _eject_cogs(self, name):
        _HANDLER.commands = {kw: cmd for kw, cmd in _HANDLER.commands.items() if cmd._cog_name != name}

    def _do_invokation(self, payload):
        '''
        # Don't use it
        '''
        self.client.loop.create_task(self._invoke_slash_command(payload))

    # Mega automated super-smart AI powered destructor-2000
    async def _auto_register_or_patch(self):
        total_posts = 0
        total_patches = 0
        bad_guilds = []
        for name, cmd in _HANDLER.commands.items():
            if cmd.registerable is not None and not cmd._auto_merged:
                cmd._auto_merged = True
                # Local registration
                if cmd.guild_ids is not None:
                    # Iterate through guilds
                    for ID in cmd.guild_ids:
                        if ID in bad_guilds:
                            continue
                        # Check if the command is registered
                        try:
                            old_cmd = self.get_guild_command_named(ID, cmd.name)
                            if old_cmd is None:
                                old_cmd = await self.fetch_guild_command_named(ID, cmd.name)
                            if old_cmd is None:
                                await self.register_guild_slash_command(ID, cmd.registerable)
                                total_posts += 1
                            elif not (old_cmd == cmd.registerable):
                                await self.edit_guild_slash_command(ID, old_cmd.id, cmd.registerable, ignore_name=True)
                                total_patches += 1
                        except Exception as e:
                            if isinstance(e, Forbidden):
                                bad_guilds.append(ID)
                            elif self._show_warnings:
                                print(f"[WARNING] Failed to build <{name}> in <{ID}>: {e}")
                # Global registration
                else:
                    try:
                        old_cmd = self.get_global_command_named(cmd.name)
                        if old_cmd is None:
                            old_cmd = await self.fetch_global_command_named(cmd.name)
                        if old_cmd is None:
                            await self.register_global_slash_command(cmd.registerable)
                            total_posts += 1
                        elif not (old_cmd == cmd.registerable):
                            await self.edit_global_slash_command(old_cmd.id, cmd.registerable, ignore_name=True)
                            total_patches += 1
                    except Exception as e:
                        if self._show_warnings:
                            print(f"[WARNING] Failed to globally build {name}: {e}")
        
        if len(bad_guilds) > 0 and self._show_warnings:
            print(f"[WARNING] Missing access: '" + "', '".join(str(ID) for ID in bad_guilds) + "'")
        
        if total_patches > 0 or total_posts > 0:
            self.client.loop.create_task(
                self._activate_event('auto_register', total_posts, total_patches)
            )

    # Cache guild commands
    async def _cache_guild_commands(self):
        for guild in self.client.guilds:
            try:
                commands = await self.fetch_guild_commands(guild.id)
                perms = await self.batch_fetch_guild_command_permissions(guild.id)
                if len(commands) > 0:
                    # Merge commands and permissions
                    merged_commands = {}
                    for cmd in commands:
                        if cmd.id in perms:
                            cmd.permissions = perms[cmd.id]
                        merged_commands[cmd.id] = cmd
                    # Put to the dict
                    self._guild_commands[guild.id] = merged_commands
            except:
                pass

    # Adding relevant listeners
    async def _on_shard_connect(self, shard_id):
        self.client._AutoShardedClient__shards[shard_id].ws._discord_parsers['INTERACTION_CREATE'] = self._do_invokation
        self.active_shard_count += 1
        if self.active_shard_count >= self.client.shard_count:
            self._global_commands = await self.fetch_global_commands()
            await self._auto_register_or_patch()
            await self._cache_guild_commands()
            self.is_ready = True
            await self._activate_event('ready')
    
    async def _on_connect(self):
        if not isinstance(self.client, discord.AutoShardedClient):
            self.client.ws._discord_parsers['INTERACTION_CREATE'] = self._do_invokation
            global_commands = await self.fetch_global_commands()
            self._global_commands = {cmd.id: cmd for cmd in global_commands}
            await self._auto_register_or_patch()
            await self._cache_guild_commands()
            self.is_ready = True
            await self._activate_event('ready')
    
    async def _on_guild_remove(self, guild):
        if guild.id in self._guild_commands:
            del self._guild_commands[guild.id]

    async def _activate_event(self, event_name, *args, **kwargs):
        '''
        # Don't use it
        '''
        func = self.events.get(event_name)
        if func is not None:
            cog = get_class(func)
            if cog is not None:
                await func(cog(self.client), *args, **kwargs)
            else:
                await func(*args, **kwargs)

    async def _invoke_slash_command(self, payload):
        '''
        # Don't use it
        '''
        inter = Interaction(self.client, payload)
        # Activate event
        await self._activate_event('slash_command', inter)
        # Invoke command
        SCR = self.commands.get(inter.data.name)
        if SCR is not None:
            try:
                await SCR.invoke(inter)
            except Exception as err:
                if 'slash_command_error' not in self.events:
                    raise err
                await self._activate_event('slash_command_error', inter, err)
    
    # Aliases
    register_global_command = register_global_slash_command
    
    register_guild_command = register_guild_slash_command

    edit_global_command = edit_global_slash_command

    edit_guild_command = edit_guild_slash_command

    delete_global_command = delete_global_slash_command

    delete_guild_command = delete_guild_slash_command
