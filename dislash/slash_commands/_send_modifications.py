from discord import utils, AllowedMentions, File, InvalidArgument
from discord.http import Route
from discord.flags import MessageFlags

from ..interactions import ActionRow


__all__ = (
    "send_with_components",
    "edit_with_components"
)


def send_message(self, channel_id, content, *, tts=False, embed=None, nonce=None,
                                    allowed_mentions=None, message_reference=None,
                                    components=None):
    r = Route('POST', '/channels/{channel_id}/messages', channel_id=channel_id)
    payload = {}

    if content:
        payload['content'] = content

    if tts:
        payload['tts'] = True

    if embed:
        payload['embed'] = embed

    if nonce:
        payload['nonce'] = nonce

    if allowed_mentions:
        payload['allowed_mentions'] = allowed_mentions

    if message_reference:
        payload['message_reference'] = message_reference
    
    if components:
        payload['components'] = components

    return self.request(r, json=payload)


def send_files(self, channel_id, *, files, content=None, tts=False, embed=None, nonce=None,
                                            allowed_mentions=None, message_reference=None,
                                            components=None):
    r = Route('POST', '/channels/{channel_id}/messages', channel_id=channel_id)
    form = []

    payload = {'tts': tts}
    if content:
        payload['content'] = content
    if embed:
        payload['embed'] = embed
    if nonce:
        payload['nonce'] = nonce
    if allowed_mentions:
        payload['allowed_mentions'] = allowed_mentions
    if message_reference:
        payload['message_reference'] = message_reference
    if components:
        payload['components'] = components

    form.append({'name': 'payload_json', 'value': utils.to_json(payload)})
    if len(files) == 1:
        file = files[0]
        form.append({
            'name': 'file',
            'value': file.fp,
            'filename': file.filename,
            'content_type': 'application/octet-stream'
        })
    else:
        for index, file in enumerate(files):
            form.append({
                'name': 'file%s' % index,
                'value': file.fp,
                'filename': file.filename,
                'content_type': 'application/octet-stream'
            })

    return self.request(r, form=form, files=files)


async def send_with_components(messageable, content=None, *,
                                            tts=False, embed=None,
                                            components=None,
                                            file=None, files=None,
                                            delete_after=None, nonce=None,
                                            allowed_mentions=None, reference=None,
                                            mention_author=None):
    channel = await messageable._get_channel()
    state = messageable._state
    content = str(content) if content is not None else None
    if embed is not None:
        embed = embed.to_dict()
    
    if components is not None:
        if len(components) > 5:
            raise InvalidArgument("components must be a list of up to 5 action rows")
        if not all(isinstance(comp, ActionRow) for comp in components):
            raise InvalidArgument("components must be a list of ActionRow")
        components = [comp.to_dict() for comp in components]

    if allowed_mentions is not None:
        if state.allowed_mentions is not None:
            allowed_mentions = state.allowed_mentions.merge(allowed_mentions).to_dict()
        else:
            allowed_mentions = allowed_mentions.to_dict()
    else:
        allowed_mentions = state.allowed_mentions and state.allowed_mentions.to_dict()

    if mention_author is not None:
        allowed_mentions = allowed_mentions or AllowedMentions().to_dict()
        allowed_mentions['replied_user'] = bool(mention_author)

    if reference is not None:
        try:
            reference = reference.to_message_reference_dict()
        except AttributeError:
            raise InvalidArgument('reference parameter must be Message or MessageReference') from None

    if file is not None and files is not None:
        raise InvalidArgument('cannot pass both file and files parameter to send()')

    if file is not None:
        if not isinstance(file, File):
            raise InvalidArgument('file parameter must be File')

        try:
            data = await send_files(state.http, channel.id, files=[file], allowed_mentions=allowed_mentions,
                                                content=content, tts=tts, embed=embed, nonce=nonce,
                                                message_reference=reference, components=components)
        finally:
            file.close()

    elif files is not None:
        if len(files) > 10:
            raise InvalidArgument('files parameter must be a list of up to 10 elements')
        elif not all(isinstance(file, File) for file in files):
            raise InvalidArgument('files parameter must be a list of File')

        try:
            data = await send_files(state.http, channel.id, files=files, content=content, tts=tts,
                                                embed=embed, nonce=nonce, allowed_mentions=allowed_mentions,
                                                message_reference=reference, components=components)
        finally:
            for f in files:
                f.close()
    else:
        data = await send_message(state.http, channel.id, content, tts=tts, embed=embed,
                                                        nonce=nonce, allowed_mentions=allowed_mentions,
                                                        message_reference=reference, components=components)

    ret = state.create_message(channel=channel, data=data)
    if delete_after is not None:
        await ret.delete(delay=delete_after)
    return ret


async def edit_with_components(message, **fields):
    try:
        content = fields['content']
    except KeyError:
        pass
    else:
        if content is not None:
            fields['content'] = str(content)

    try:
        embed = fields['embed']
    except KeyError:
        pass
    else:
        if embed is not None:
            fields['embed'] = embed.to_dict()
    
    try:
        components = fields['components']
    except KeyError:
        pass
    else:
        if components is not None:
            fields['components'] = [comp.to_dict() for comp in components]

    try:
        suppress = fields.pop('suppress')
    except KeyError:
        pass
    else:
            flags = MessageFlags._from_value(message.flags.value)
            flags.suppress_embeds = suppress
            fields['flags'] = flags.value

    delete_after = fields.pop('delete_after', None)

    try:
        allowed_mentions = fields.pop('allowed_mentions')
    except KeyError:
        pass
    else:
        if allowed_mentions is not None:
            if message._state.allowed_mentions is not None:
                allowed_mentions = message._state.allowed_mentions.merge(allowed_mentions).to_dict()
            else:
                allowed_mentions = allowed_mentions.to_dict()
            fields['allowed_mentions'] = allowed_mentions

    if fields:
        data = await message._state.http.edit_message(message.channel.id, message.id, **fields)
        message._update(data)

    if delete_after is not None:
        await message.delete(delay=delete_after)
