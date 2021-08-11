from discord import (
    InvalidArgument,
    AllowedMentions,
    File,
    GuildSticker, StickerItem,
    Embed,
    Message, MessageReference, PartialMessage, MessageFlags,
    Attachment
)

from discord.ui import View
from discord.utils import MISSING

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    Union,
    overload
)

from ...interactions import ActionRow


__all__ = (
    "send",
    "edit"
)


@overload
async def send(
    self,
    content: Optional[str] = ...,
    *,
    tts: bool = ...,
    embed: Embed = ...,
    file: File = ...,
    stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
    delete_after: float = ...,
    nonce: Union[str, int] = ...,
    allowed_mentions: AllowedMentions = ...,
    reference: Union[Message, MessageReference, PartialMessage] = ...,
    mention_author: bool = ...,
    view: View = ...,
    components: list = ...,
) -> Message:
    ...


@overload
async def send(
    self,
    content: Optional[str] = ...,
    *,
    tts: bool = ...,
    embed: Embed = ...,
    files: List[File] = ...,
    stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
    delete_after: float = ...,
    nonce: Union[str, int] = ...,
    allowed_mentions: AllowedMentions = ...,
    reference: Union[Message, MessageReference, PartialMessage] = ...,
    mention_author: bool = ...,
    view: View = ...,
    components: list = ...,
) -> Message:
    ...


@overload
async def send(
    self,
    content: Optional[str] = ...,
    *,
    tts: bool = ...,
    embeds: List[Embed] = ...,
    file: File = ...,
    stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
    delete_after: float = ...,
    nonce: Union[str, int] = ...,
    allowed_mentions: AllowedMentions = ...,
    reference: Union[Message, MessageReference, PartialMessage] = ...,
    mention_author: bool = ...,
    view: View = ...,
    components: list = ...,
) -> Message:
    ...


@overload
async def send(
    self,
    content: Optional[str] = ...,
    *,
    tts: bool = ...,
    embeds: List[Embed] = ...,
    files: List[File] = ...,
    stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
    delete_after: float = ...,
    nonce: Union[str, int] = ...,
    allowed_mentions: AllowedMentions = ...,
    reference: Union[Message, MessageReference, PartialMessage] = ...,
    mention_author: bool = ...,
    view: View = ...,
    components: list = ...,
) -> Message:
    ...


async def send(
    self,
    content=None,
    *,
    tts=None,
    embed=None,
    embeds=None,
    file=None,
    files=None,
    stickers=None,
    delete_after=None,
    nonce=None,
    allowed_mentions=None,
    reference=None,
    mention_author=None,
    view=None,
    components=None,
):
    """|coro|

    Sends a message to the destination with the content given.

    The content must be a type that can convert to a string through ``str(content)``.
    If the content is set to ``None`` (the default), then the ``embed`` parameter must
    be provided.

    To upload a single file, the ``file`` parameter should be used with a
    single :class:`~discord.File` object. To upload multiple files, the ``files``
    parameter should be used with a :class:`list` of :class:`~discord.File` objects.
    **Specifying both parameters will lead to an exception**.

    To upload a single embed, the ``embed`` parameter should be used with a
    single :class:`~discord.Embed` object. To upload multiple embeds, the ``embeds``
    parameter should be used with a :class:`list` of :class:`~discord.Embed` objects.
    **Specifying both parameters will lead to an exception**.

    Parameters
    ------------
    content: Optional[:class:`str`]
        The content of the message to send.
    tts: :class:`bool`
        Indicates if the message should be sent using text-to-speech.
    embed: :class:`~discord.Embed`
        The rich embed for the content.
    file: :class:`~discord.File`
        The file to upload.
    files: List[:class:`~discord.File`]
        A list of files to upload. Must be a maximum of 10.
    nonce: :class:`int`
        The nonce to use for sending this message. If the message was successfully sent,
        then the message will have a nonce with this value.
    delete_after: :class:`float`
        If provided, the number of seconds to wait in the background
        before deleting the message we just sent. If the deletion fails,
        then it is silently ignored.
    allowed_mentions: :class:`~discord.AllowedMentions`
        Controls the mentions being processed in this message. If this is
        passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
        The merging behaviour only overrides attributes that have been explicitly passed
        to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
        If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
        are used instead.

        .. versionadded:: 1.4

    reference: Union[:class:`~discord.Message`, :class:`~discord.MessageReference`, :class:`~discord.PartialMessage`]
        A reference to the :class:`~discord.Message` to which you are replying, this can be created using
        :meth:`~discord.Message.to_reference` or passed directly as a :class:`~discord.Message`. You can control
        whether this mentions the author of the referenced message using the :attr:`~discord.AllowedMentions.replied_user`
        attribute of ``allowed_mentions`` or by setting ``mention_author``.

        .. versionadded:: 1.6

    mention_author: Optional[:class:`bool`]
        If set, overrides the :attr:`~discord.AllowedMentions.replied_user` attribute of ``allowed_mentions``.

        .. versionadded:: 1.6
    view: :class:`discord.ui.View`
        A Discord UI View to add to the message.
    embeds: List[:class:`~discord.Embed`]
        A list of embeds to upload. Must be a maximum of 10.

        .. versionadded:: 2.0
    stickers: Sequence[Union[:class:`~discord.GuildSticker`, :class:`~discord.StickerItem`]]
        A list of stickers to upload. Must be a maximum of 3.

        .. versionadded:: 2.0

    Raises
    --------
    ~discord.HTTPException
        Sending the message failed.
    ~discord.Forbidden
        You do not have the proper permissions to send the message.
    ~discord.InvalidArgument
        The ``files`` list is not of the appropriate size,
        you specified both ``file`` and ``files``,
        or you specified both ``embed`` and ``embeds``,
        or the ``reference`` object is not a :class:`~discord.Message`,
        :class:`~discord.MessageReference` or :class:`~discord.PartialMessage`.

    Returns
    ---------
    :class:`~discord.Message`
        The message that was sent.
    """

    channel = await self._get_channel()
    state = self._state
    content = str(content) if content is not None else None
    _components = None

    if embed is not None and embeds is not None:
        raise InvalidArgument('cannot pass both embed and embeds parameter to send()')

    if embed is not None:
        embed = embed.to_dict()

    elif embeds is not None:
        if len(embeds) > 10:
            raise InvalidArgument('embeds parameter must be a list of up to 10 elements')
        embeds = [embed.to_dict() for embed in embeds]

    if stickers is not None:
        stickers = [sticker.id for sticker in stickers]

    if allowed_mentions is None:
        allowed_mentions = state.allowed_mentions and state.allowed_mentions.to_dict()

    elif state.allowed_mentions is not None:
        allowed_mentions = state.allowed_mentions.merge(allowed_mentions).to_dict()
    else:
        allowed_mentions = allowed_mentions.to_dict()
    if mention_author is not None:
        allowed_mentions = allowed_mentions or AllowedMentions().to_dict()
        allowed_mentions['replied_user'] = bool(mention_author)

    if reference is not None:
        try:
            reference = reference.to_message_reference_dict()
        except AttributeError:
            raise InvalidArgument('reference parameter must be Message, MessageReference, or PartialMessage') from None

    if view:
        if not hasattr(view, '__discord_ui_view__'):
            raise InvalidArgument(f'view parameter must be View not {view.__class__!r}')

        _components = view.to_components()
    else:
        _components = None

    if components:
        # This is not needed, but some users still prefer
        # dislash style of sending components so yeah
        if len(components) > 5:
            raise InvalidArgument("components must be a list of up to 5 action rows")
        wrapped = []
        for comp in components:
            if isinstance(comp, ActionRow):
                wrapped.append(comp)
            else:
                wrapped.append(ActionRow(comp))
        components = _components or []
        for comp in wrapped:
            components.append(comp.to_dict())

    if file is not None and files is not None:
        raise InvalidArgument('cannot pass both file and files parameter to send()')

    if file is not None:
        if not isinstance(file, File):
            raise InvalidArgument('file parameter must be File')

        try:
            data = await state.http.send_files(
                channel.id,
                files=[file],
                allowed_mentions=allowed_mentions,
                content=content,
                tts=tts,
                embed=embed,
                embeds=embeds,
                nonce=nonce,
                message_reference=reference,
                stickers=stickers,
                components=components,
            )
        finally:
            file.close()

    elif files is not None:
        if len(files) > 10:
            raise InvalidArgument('files parameter must be a list of up to 10 elements')
        elif not all(isinstance(file, File) for file in files):
            raise InvalidArgument('files parameter must be a list of File')

        try:
            data = await state.http.send_files(
                channel.id,
                files=files,
                content=content,
                tts=tts,
                embed=embed,
                embeds=embeds,
                nonce=nonce,
                allowed_mentions=allowed_mentions,
                message_reference=reference,
                stickers=stickers,
                components=components,
            )
        finally:
            for f in files:
                f.close()
    else:
        data = await state.http.send_message(
            channel.id,
            content,
            tts=tts,
            embed=embed,
            embeds=embeds,
            nonce=nonce,
            allowed_mentions=allowed_mentions,
            message_reference=reference,
            stickers=stickers,
            components=components,
        )

    ret = state.create_message(channel=channel, data=data)
    if view:
        state.store_view(view, ret.id)

    if delete_after is not None:
        await ret.delete(delay=delete_after)
    return ret


@overload
async def edit(
    self,
    *,
    content: Optional[str] = ...,
    embed: Optional[Embed] = ...,
    attachments: List[Attachment] = ...,
    suppress: bool = ...,
    delete_after: Optional[float] = ...,
    allowed_mentions: Optional[AllowedMentions] = ...,
    view: Optional[View] = ...,
    components: Optional[list] = ...,
) -> None:
    ...


@overload
async def edit(
    self,
    *,
    content: Optional[str] = ...,
    embeds: List[Embed] = ...,
    attachments: List[Attachment] = ...,
    suppress: bool = ...,
    delete_after: Optional[float] = ...,
    allowed_mentions: Optional[AllowedMentions] = ...,
    view: Optional[View] = ...,
    components: Optional[list] = ...,
) -> None:
    ...


async def edit(
    self,
    content: Optional[str] = MISSING,
    embed: Optional[Embed] = MISSING,
    embeds: List[Embed] = MISSING,
    attachments: List[Attachment] = MISSING,
    suppress: bool = MISSING,
    delete_after: Optional[float] = None,
    allowed_mentions: Optional[AllowedMentions] = MISSING,
    view: Optional[View] = MISSING,
    components: Optional[list] = MISSING,
) -> None:
    """|coro|

    Edits the message.

    The content must be able to be transformed into a string via ``str(content)``.

    .. versionchanged:: 1.3
        The ``suppress`` keyword-only parameter was added.

    Parameters
    -----------
    content: Optional[:class:`str`]
        The new content to replace the message with.
        Could be ``None`` to remove the content.
    embed: Optional[:class:`Embed`]
        The new embed to replace the original with.
        Could be ``None`` to remove the embed.
    embeds: List[:class:`Embed`]
        The new embeds to replace the original with. Must be a maximum of 10.
        To remove all embeds ``[]`` should be passed.

        .. versionadded:: 2.0
    attachments: List[:class:`Attachment`]
        A list of attachments to keep in the message. If ``[]`` is passed
        then all attachments are removed.
    suppress: :class:`bool`
        Whether to suppress embeds for the message. This removes
        all the embeds if set to ``True``. If set to ``False``
        this brings the embeds back if they were suppressed.
        Using this parameter requires :attr:`~.Permissions.manage_messages`.
    delete_after: Optional[:class:`float`]
        If provided, the number of seconds to wait in the background
        before deleting the message we just edited. If the deletion fails,
        then it is silently ignored.
    allowed_mentions: Optional[:class:`~discord.AllowedMentions`]
        Controls the mentions being processed in this message. If this is
        passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
        The merging behaviour only overrides attributes that have been explicitly passed
        to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
        If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
        are used instead.

        .. versionadded:: 1.4
    view: Optional[:class:`~discord.ui.View`]
        The updated view to update this message with. If ``None`` is passed then
        the view is removed.

    Raises
    -------
    HTTPException
        Editing the message failed.
    Forbidden
        Tried to suppress a message without permissions or
        edited a message's content or embed that isn't yours.
    ~discord.InvalidArgument
        You specified both ``embed`` and ``embeds``
    """

    _components = None
    payload: Dict[str, Any] = {}
    if content is not MISSING:
        payload['content'] = str(content) if content is not None else None
    if embed is not MISSING and embeds is not MISSING:
        raise InvalidArgument('cannot pass both embed and embeds parameter to edit()')

    if embed is not MISSING:
        payload['embeds'] = [] if embed is None else [embed.to_dict()]
    elif embeds is not MISSING:
        payload['embeds'] = [e.to_dict() for e in embeds]

    if suppress is not MISSING:
        flags = MessageFlags._from_value(self.flags.value)
        flags.suppress_embeds = suppress
        payload['flags'] = flags.value

    if allowed_mentions is MISSING:
        if self._state.allowed_mentions is not None and self.author.id == self._state.self_id:
            payload['allowed_mentions'] = self._state.allowed_mentions.to_dict()
    elif allowed_mentions is not None:
        if self._state.allowed_mentions is not None:
            payload['allowed_mentions'] = self._state.allowed_mentions.merge(allowed_mentions).to_dict()
        else:
            payload['allowed_mentions'] = allowed_mentions.to_dict()

    if attachments is not MISSING:
        payload['attachments'] = [a.to_dict() for a in attachments]

    if view is not MISSING:
        self._state.prevent_view_updates_for(self.id)
        _components = view.to_components() if view else []
    if components is not MISSING:
        # Once again, this is for those who prefer dislash.py style
        if components:
            _components = _components or []
            for comp in components:
                if isinstance(comp, ActionRow):
                    _components.append(comp.to_dict())
                else:
                    _components.append(ActionRow(comp).to_dict())
        else:
            _components = _components or []

    payload["components"] = _components or []

    if payload:
        data = await self._state.http.edit_message(self.channel.id, self.id, **payload)
        self._update(data)

    if view and not view.is_finished():
        self._state.store_view(view, self.id)

    if delete_after is not None:
        await self.delete(delay=delete_after)
