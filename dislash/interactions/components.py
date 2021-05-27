import discord


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


class Component:
    """
    The base class for message components
    """
    def __init__(self, type: int):
        self.type = type


class Button(Component):
    """
    Builds a button.

    Parameters
    ----------
    style : :class:`ButtonStyle`
        Style of the button
    label : :class:`str`
        Button text
    emoji : :class:`discord.PartialEmoji`
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
        if custom_id is None:
            if url is None:
                raise discord.InvalidArgument("url or custom_id must be specified")
            if style != ButtonStyle.link:
                raise discord.InvalidArgument("if you specify url, the style must be ButtonStyle.link")
        elif url is not None:
            raise discord.InvalidArgument("you can't specify both url and custom_id")
        elif style == ButtonStyle.link:
            raise discord.InvalidArgument("style 'link' expects url to be specified")

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
        self.components = components
    
    def __repr__(self):
        return "<ActionRow buttons={0.components!r}>".format(self)

    @property
    def buttons(self):
        return self.components
    
    @classmethod
    def from_dict(cls, data: dict):
        buttons = [Button.from_dict(elem) for elem in data.get("components", [])]
        return ActionRow(*buttons)

    def add_button(self, button: Button):
        self.components.append(button)
    
    def to_dict(self):
        return {
            "type": self.type,
            "components": [comp.to_dict() for comp in self.components]
        }
