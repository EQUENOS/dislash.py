import discord
import re


__all__ = (
    "auto_rows",
    "ComponentType",
    "ButtonStyle",
    "Component",
    "Button",
    "ActionRow",
    "MenuOption",
    "SelectMenu"
)

# I don't like this solution for default custom_ids...
ID_SOURCE = 0
MAX_ID = 25


def _partial_emoji_converter(argument: str):
    if len(argument) < 5:
        # Sometimes unicode emojis are actually more than 1 symbol
        return discord.PartialEmoji(name=argument)
    
    match = re.match(r'<(a?):([a-zA-Z0-9\_]+):([0-9]+)>$', argument)

    if match:
        emoji_animated = bool(match.group(1))
        emoji_name = match.group(2)
        emoji_id = int(match.group(3))

        return discord.PartialEmoji(name=emoji_name, animated=emoji_animated, id=emoji_id)

    raise discord.InvalidArgument(f"Failed to convert {argument} to PartialEmoji")


def _component_factory(data: dict):
    _type = data.get("type")
    if _type == 1:
        return ActionRow.from_dict(data)
    if _type == 2:
        return Button.from_dict(data)
    if _type == 3:
        return SelectMenu.from_dict(data)


def auto_rows(*buttons, max_in_row: int=5):
    """
    Distributes buttons across multiple rows
    and returns the list of rows.
    Example
    -------
    ::

        rows = auto_rows(
            Button(label="Red", custom_id="red", style=4),
            Button(label="Green", custom_id="green", style=3),
            max_in_row=1
        )
        await ctx.send("Buttons", components=rows)
    
    Parameters
    ----------
    buttons : List[:class:`Button`]
        a list of buttons to distribute
    max_in_row : :class:`int`
        limit of buttons in a single row. Must be between 1 and 5.
    
    Returns
    -------
    List[:class:`ActionRow`]
        the list of rows with buttons
    """
    if not (1 <= max_in_row <= 5):
        raise discord.InvalidArgument("max_in_row parameter should be between 1 and 5.")
    rows = []
    for i in range(0, len(buttons), max_in_row):
        rows.append(ActionRow(*buttons[i:i + max_in_row]))
    return rows


class ComponentType:
    ActionRow = 1
    Button = 2
    SelectMenu = 3


class ButtonStyle:
    """
    Attributes
    ----------
    blurple = 1
    grey    = 2
    green   = 3
    red     = 4
    link    = 5
    """
    primary   = 1
    blurple   = 1

    secondary = 2
    grey      = 2
    gray      = 2

    success   = 3
    green     = 3

    danger    = 4
    red       = 4

    link      = 5

# Beta
class MenuOption:
    __slots__ = ("label", "value")

    def __init__(self, label: str, value):
        self.label = label
        self.value = value
    
    def __repr__(self):
        return "<OptionSelect label='{0.label}' value={0.value}>".format(self)

    @classmethod
    def from_dict(cls, data: dict):
        return MenuOption(label=data.get("label"), value=data.get("value"))
    
    def to_dict(self):
        return {"label": self.label, "value": self.value}


class Component:
    """
    The base class for message components
    """
    def __init__(self, type: int):
        self.type = type

# Beta
class SelectMenu(Component):
    def __init__(self, *, custom_id: str, placeholder: str=None, min_values: int=1, max_values: int=1, options: list=None):
        super().__init__(3)
        self.custom_id = custom_id
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.options = options or []
    
    def __repr__(self):
        desc = " ".join(f"{kw}={v}" for kw, v in self.to_dict().items())
        return f"<SelectMenu {desc}>"

    def add_option(self, *, label: str, value):
        self.options.append(
            MenuOption(label=label, value=value)
        )

    @classmethod
    def from_dict(cls, data: dict):
        options = data.get("options", [])
        return SelectMenu(
            custom_id=data.get("custom_id"),
            placeholder=data.get("placeholder"),
            min_values=data.get("min_values", 1),
            max_values=data.get("max_values", 1),
            options=[MenuOption.from_dict(o) for o in options]
        )

    def to_dict(self):
        payload = {
            "type": self.type,
            "custom_id": self.custom_id,
            "min_values": self.min_values,
            "max_values": self.max_values,
            "options": [o.to_dict() for o in self.options]
        }
        if self.placeholder:
            payload["placeholder"] = self.placeholder
        return payload


class Button(Component):
    """
    Builds a button.

    Parameters
    ----------
    style : :class:`ButtonStyle`
        Style of the button
    label : :class:`str`
        Button text
    emoji : :class:`str` | :class:`discord.PartialEmoji`
        Button emoji
    custom_id : :class:`str`
        You should set it by yourself, it's not a snowflake.
        If button style is not :class:`ButtonStyle.link`, this is
        a required field
    url : :class:`str`
        If button style is :class:`ButtonStyle.link`, this is
        a required field.
    disabled : :class:`bool`
        Whether the button is disabled or not. Defaults to false.
    """
    def __init__(self, *, style: ButtonStyle, label: str=None, emoji: discord.PartialEmoji=None,
                                    custom_id: str=None, url: str=None, disabled: bool=False):
        global ID_SOURCE # Ugly as hell

        if custom_id is None:
            if url is None:
                custom_id = str(ID_SOURCE)
                ID_SOURCE = (ID_SOURCE + 1) % MAX_ID
                # raise discord.InvalidArgument("url or custom_id must be specified")
            elif style != ButtonStyle.link:
                raise discord.InvalidArgument("if you specify url, the style must be ButtonStyle.link")
        elif url is not None:
            raise discord.InvalidArgument("you can't specify both url and custom_id")
        elif style == ButtonStyle.link:
            raise discord.InvalidArgument("style 'link' expects url to be specified")
        
        if isinstance(emoji, str):
            emoji = _partial_emoji_converter(emoji)

        super().__init__(2)
        self.style = style
        self.label = label
        self.emoji = emoji
        self.custom_id = custom_id
        self.url = url
        self.disabled = disabled
    
    def __repr__(self):
        desc = " ".join(f"{kw}={v}" for kw, v in self.to_dict().items())
        return f"<Button {desc}>"

    @property
    def id(self):
        return self.custom_id

    @classmethod
    def from_dict(cls, data: dict):
        if "emoji" in data:
            emoji = discord.PartialEmoji.from_dict(data["emoji"])
        else:
            emoji = None
        return Button(
            style=data.get("style"),
            label=data.get("label"),
            emoji=emoji,
            custom_id=data.get("custom_id"),
            url=data.get("url"),
            disabled=data.get("disabled", False)
        )

    def to_dict(self):
        payload = {
            "type": self.type,
            "style": self.style
        }
        if self.label is not None:
            payload["label"] = self.label
        if self.emoji is not None:
            payload["emoji"] = self.emoji.to_dict()
        if self.custom_id is not None:
            payload["custom_id"] = self.custom_id
        if self.url is not None:
            payload["url"] = self.url
        if self.disabled:
            payload["disabled"] = self.disabled
        return payload


class ActionRow(Component):
    """
    Represents an action row. Action rows are basically
    shelves for buttons.

    Parameters
    ----------
    components : :class:`List[Button]`
        a list of up to 5 buttons to place in a row
    """
    def __init__(self, *components):
        self._limit = 5
        if len(components) > self._limit:
            raise discord.InvalidArgument(f"components must be a list of up to {self._limit} elements")
        if not all(isinstance(comp, Component) for comp in components):
            raise discord.InvalidArgument("components must be a list of Component")
        
        super().__init__(1)
        self.components = list(components)
    
    def __repr__(self):
        return "<ActionRow components={0.components!r}>".format(self)

    @property
    def buttons(self):
        return self.components
    
    @classmethod
    def from_dict(cls, data: dict):
        buttons = [_component_factory(elem) for elem in data.get("components", [])]
        return ActionRow(*buttons)

    def to_dict(self):
        return {
            "type": self.type,
            "components": [comp.to_dict() for comp in self.components]
        }

    def disable_buttons(self):
        """
        Sets ``disabled`` to ``True`` for all buttons in this row.
        """
        for component in self.components:
            if component.type == ComponentType.Button:
                component.disabled = True

    def enable_buttons(self):
        """
        Sets ``disabled`` to ``False`` for all buttons in this row.
        """
        for component in self.components:
            if component.type == ComponentType.Button:
                component.disabled = False

    def add_button(self, *, style: ButtonStyle, label: str=None, emoji: str=None,
                        custom_id: str=None, url: str=None, disabled: bool=False):
        self.components.append(
            Button(
                style=style,
                label=label,
                emoji=emoji,
                custom_id=custom_id,
                url=url,
                disabled=disabled
            )
        )
    
    def add_menu(self, *, custom_id: str, placeholder: str=None, min_values: int=1, max_values: int=1, options: list=None):
        self.components.append(
            SelectMenu(
                custom_id=custom_id,
                placeholder=placeholder,
                min_values=min_values,
                max_values=max_values,
                options=options
            )
        )
