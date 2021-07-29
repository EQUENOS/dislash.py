from typing import Union, List, Any
import discord
import re


__all__ = (
    "Type",
    "OptionChoice",
    "Option",
    "SlashCommand",
    "SlashCommandPermissions",
    "RawCommandPermission"
)


class Type:
    """
    Attributes
    ----------
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
    NUMBER = 10
    """
    SUB_COMMAND       = 1
    SUB_COMMAND_GROUP = 2
    STRING            = 3
    INTEGER           = 4
    BOOLEAN           = 5
    USER              = 6
    CHANNEL           = 7
    ROLE              = 8
    MENTIONABLE       = 9
    NUMBER            = 10


class OptionChoice:
    """
    Parameters
    ----------
    name : str
        the name of the option-choice (visible to users)
    value : str or int
        the value of the option-choice
    """

    def __init__(self, name: str, value: Any):
        self.name = name
        self.value = value

    def __repr__(self):
        return "<OptionChoice name='{0.name}' value={0.value}>".format(self)

    def __eq__(self, other):
        return (
            self.name == other.name and
            self.value == other.value
        )


class Option:
    """
    Parameters
    ----------
    name : :class:`str`
        option's name
    description : :class:`str`
        option's description
    type : :class:`Type`
        the option type, e.g. ``Type.USER``, see :ref:`option_type`
    required : :class:`bool`
        whether this option is required or not
    choices : List[:class:`OptionChoice`]
        the list of option choices, type :ref:`option_choice`
    options : List[:class:`Option`]
        the list of sub options. You can only specify this parameter if
        the ``type`` is :class:`Type.SUB_COMMAND` or :class:`Type.SUB_COMMAND_GROUP`
    """

    __slots__ = ("name", "description", "type", "required", "choices", "options", "_choice_connectors")

    def __init__(self, name: str, description: str=None, type: int=None, required: bool=False, choices: List[OptionChoice]=None, options: list=None):
        assert name.islower(), f"Option name {name!r} must be lowercase"
        self.name = name
        self.description = description
        self.type = type or 3
        self.required = required
        self.choices = choices or []
        if options is not None:
            if self.type == 1:
                for option in options:
                    if option.type < 3:
                        raise ValueError('Unexpected sub_command in a sub_command')
            elif self.type == 2:
                for option in options:
                    if option.type != 1:
                        raise ValueError('Expected sub_command in this sub_command_group')
        self.options = options or []
        self._choice_connectors = {}
        # Wrap choices
        for i, choice in enumerate(self.choices):
            if self.type == Type.INTEGER:
                if not isinstance(choice.value, int):
                    self._choice_connectors[i] = choice.value
                    choice.value = i
            elif self.type == Type.STRING:
                if not isinstance(choice.value, str):
                    valid_value = f"option_choice_{i}"
                    self._choice_connectors[valid_value] = choice.value
                    choice.value = valid_value

    def __repr__(self):
        string = "name='{0.name}' description='{0.description} type={0.type} required={0.required}".format(self)
        if len(self.options) > 0:
            string = f"{string} options={self.options}"
        if len(self.choices) > 0:
            string = f"{string} choices={self.choices}"
        return f"<Option {string}>"

    def __eq__(self, other):
        return (
            self.name == other.name and
            self.description == other.description and
            self.type == other.type and
            self.required == other.required and
            self.choices == other.choices and
            self.options == other.options
        )

    @classmethod
    def from_dict(cls, payload: dict):
        if 'options' in payload:
            payload['options'] = [Option.from_dict(p) for p in payload['options']]
        if 'choices' in payload:
            payload['choices'] = [OptionChoice(**p) for p in payload['choices']]
        return Option(**payload)

    def add_choice(self, name: str, value: Any):
        '''
        Adds an OptionChoice to the list of current choices

        Parameters are the same as for :class:`OptionChoice`
        '''
        # Wrap the value
        true_value = value
        if self.type == Type.STRING:
            if not isinstance(value, str):
                true_value = f"option_choice_{len(self._choice_connectors)}"
                self._choice_connectors[true_value] = value
        elif self.type == Type.INTEGER:
            if not isinstance(value, int):
                true_value = len(self._choice_connectors)
                self._choice_connectors[true_value] = value
        # Add an option choice
        self.choices.append(OptionChoice(name=name, value=true_value))

    def add_option(self, name: str, description: str=None, type: int=None, required: bool=False, choices: List[OptionChoice]=None, options: list=None):
        '''
        Adds an option to the current list of options

        Parameters are the same as for :class:`Option`
        '''
        if self.type == 1:
            if type < 3:
                raise ValueError('sub_command can only be nested in a sub_command_group')
        elif self.type == 2:
            if type != 1:
                raise ValueError('Expected sub_command in this sub_command_group')
        self.options.append(
            Option(
                name=name,
                description=description,
                type=type,
                required=required,
                choices=choices,
                options=options
            )
        )

    def to_dict(self):
        payload = {
            'name': self.name,
            'description': self.description,
            'type': self.type
        }
        if self.required:
            payload['required'] = True
        if len(self.choices) > 0:
            payload['choices'] = [c.__dict__ for c in self.choices]
        if len(self.options) > 0:
            payload['options'] = [o.to_dict() for o in self.options]
        return payload


class SlashCommand:
    """
    A base class for building slash-commands.

    Parameters
    ----------
    name : :class:`str`
        The command name
    description : :class:`str`
        The command description (it'll be displayed by discord)
    options : List[Option]
        The options of the command. See :ref:`option`
    default_permission : :class:`bool`
        Whether the command is enabled by default when the app is added to a guild
    """

    def __init__(self, name: str, description: str, options: list=None,
                                default_permission: bool=True, **kwargs):
        self.id = kwargs.pop('id', None)
        if self.id is not None:
            self.id = int(self.id)
        self.application_id = kwargs.pop('application_id', None)
        if self.application_id is not None:
            self.application_id = int(self.application_id)
        
        assert re.match(r"^[\w-]{1,32}$", name) is not None and name.islower(),\
            f"Slash command name {name!r} should consist of these symbols: a-z, 0-9, -, _"

        self.name = name
        self.description = description
        self.options = options or []
        self.default_permission = default_permission
        self.permissions = SlashCommandPermissions()

    def __repr__(self):
        return "<SlashCommand name='{0.name}' description='{0.description}' options={0.options}>".format(self)

    def __eq__(self, other):
        return (
            self.name == other.name and
            self.description == other.description and
            self.options == other.options
        )

    @classmethod
    def from_dict(cls, payload: dict):
        if 'options' in payload:
            payload['options'] = [Option.from_dict(p) for p in payload['options']]
        return SlashCommand(**payload)

    def add_option(self, name: str, description: str=None, type: int=None, required: bool=False, choices: List[OptionChoice]=None, options: list=None):
        '''
        Adds an option to the current list of options

        Parameters are the same as for :class:`Option`
        '''
        self.options.append(
            Option(
                name=name,
                description=description,
                type=type,
                required=required,
                choices=choices,
                options=options
            )
        )

    def to_dict(self, *, hide_name=False):
        res = {
            "description": self.description,
            "options": [o.to_dict() for o in self.options]
        }
        if not self.default_permission:
            res["default_permission"] = False
        if not hide_name:
            res["name"] = self.name
        return res


# Permissions
class SlashCommandPermissions:
    """
    Represents slash command permissions.
    Roughly equivalent to a list of :class:`RawCommandPermission`

    Slash command permissions are checked on the server side.
    Only local slash commands can have this type of permissions.

    Obtainable via :class:`SlashCommand.permissions`

    Parameters
    ----------
    raw_permissions : List[RawCommandPermission]
        a list of :class:`RawCommandPermission`.
        However, :meth:`from_pairs` or :meth:`from_ids`
        might be more convenient.
    """

    def __init__(self, raw_permissions: list=None):
        self.permissions = raw_permissions or []

    def __repr__(self):
        return "<SlashCommandPermissions permissions={0.permissions!r}>".format(self)

    @classmethod
    def from_pairs(cls, permissions: dict):
        """
        Creates :class:`SlashCommandPermissions` using
        instances of :class:`discord.Role` and :class:`discord.User`

        Parameters
        ----------
        permissions : :class:`dict`
            a dictionary of {:class:`Role | User`: :class:`bool`}
        """
        raw_perms = []
        for target, perm in permissions.items():
            raw_perms.append(RawCommandPermission.from_pair(target, perm))
        return SlashCommandPermissions(raw_perms)

    @classmethod
    def from_ids(cls, role_perms: dict=None, user_perms: dict=None):
        """
        Creates :class:`SlashCommandPermissions` from
        2 dictionaries of IDs and permissions.

        Parameters
        ----------
        role_perms : :class:`dict`
            a dictionary of {``role_id``: :class:`bool`}
        user_perms : :class:`dict`
            a dictionary of {``user_id``: :class:`bool`}
        """
        role_perms = role_perms or {}
        user_perms = user_perms or {}
        raw_perms = []
        for role_id, perm in role_perms.items():
            raw_perms.append(RawCommandPermission(role_id, 1, perm))
        for user_id, perm in user_perms.items():
            raw_perms.append(RawCommandPermission(user_id, 2, perm))
        return SlashCommandPermissions(raw_perms)

    @classmethod
    def from_dict(cls, data: dict):
        return SlashCommandPermissions([
            RawCommandPermission.from_dict(perm)
            for perm in data["permissions"]
        ])

    def to_dict(self):
        return {
            "permissions": [perm.to_dict() for perm in self.permissions]
        }


class RawCommandPermission:
    """
    Represents command permissions for a role or a user.

    Attributes
    ----------
    id : :class:`int`
        ID of a target
    type : :class:`int`
        1 if target is a role; 2 if target is a user
    permission : :class:`bool`
        allow or deny the access to the command
    """

    __slots__ = ("id", "type", "permission")

    def __init__(self, id: int, type: int, permission: bool):
        self.id = id
        self.type = type
        self.permission = permission

    def __repr__(self):
        return "<RawCommandPermission id={0.id} type={0.type} permission={0.permission}>".format(self)

    @classmethod
    def from_pair(cls, target: Union[discord.Role, discord.User], permission: bool):
        if not isinstance(target, (discord.Role, discord.User)):
            raise discord.InvalidArgument("target should be Role or User")
        if not isinstance(permission, bool):
            raise discord.InvalidArgument("permission should be bool")
        return RawCommandPermission(
            id=target.id,
            type=1 if isinstance(target, discord.Role) else 2,
            permission=permission
        )

    @classmethod
    def from_dict(cls, data: dict):
        return RawCommandPermission(
            id=data["id"],
            type=data["type"],
            permission=data["permission"]
        )

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "permission": self.permission
        }
