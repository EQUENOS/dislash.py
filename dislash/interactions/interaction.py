import asyncio
import datetime
import discord
from discord.http import Route
from discord.utils import snowflake_time
from .message_components import ActionRow


__all__ = (
    "InteractionType",
    "ResponseType",
    "BaseInteraction"
)


class InteractionType:
    Ping               = 1
    ApplicationCommand = 2
    MessageComponent   = 3


class ResponseType:
    """
    All possible response type values. Used in :class:`Interaction.reply`

    Attributes
    ----------
    Pong = 1
        ACK a Ping
    ChannelMessageWithSource = 4
        Respond to an interaction with a message
    AcknowledgeWithSource = 5
        ACK an interaction and edit a response later, the user sees a loading state
    DeferredUpdateMessage = 6
        For components, ACK an interaction and edit the original message later;
        the user does not see a loading state
    UpdateMessage = 7
        For components, edit the message the component was attached to
    """
    Pong                     = 1
    Acknowledge              = 1
    ChannelMessage           = 3
    ChannelMessageWithSource = 4
    AcknowledgeWithSource    = 5
    DeferredUpdateMessage    = 6
    UpdateMessage            = 7


class BaseInteraction:
    """
    The base class for all interactions
    """

    def __init__(self, client, data: dict):
        state = client._connection

        self.id = int(data["id"])
        self.application_id = int(data["application_id"])
        self.type = data["type"]
        self.token = data["token"]
        self.version = data["version"]

        if "guild_id" in data:
            self.guild = client.get_guild(int(data["guild_id"]))
            self.author = discord.Member(
                data=data["member"],
                guild=self.guild,
                state=state
            )
        else:
            self.guild = None
            self.author = discord.User(
                state=state,
                data=data["user"]
            )
        
        if "channel_id" in data:
            self.channel = client.get_channel(int(data["channel_id"]))
        else:
            self.channel = None
        
        self.editable = False
        self._client = client
        self._sent = False
        self._webhook = None

    @property
    def webhook(self):
        if self._webhook is None:
            self._webhook = discord.Webhook(
                {"id": self._client.user.id, "type": 1, "token": self.token},
                adapter=discord.AsyncWebhookAdapter(self._client.http._HTTPClient__session)
            )
        return self._webhook
    
    @property
    def created_at(self):
        return snowflake_time(self.id)
    
    @property
    def expired(self):
        if self._sent:
            return datetime.datetime.utcnow() - self.created_at > datetime.timedelta(minutes=15)
        else:
            return datetime.datetime.utcnow() - self.created_at > datetime.timedelta(seconds=3)

    async def reply(self, content=None, *,  embed=None, embeds=None,
                                            components=None,
                                            file=None, files=None,
                                            tts=False, hide_user_input=False,
                                            ephemeral=False, delete_after=None,
                                            allowed_mentions=None, type=None,
                                            fetch_response_message=True):
        """
        Creates an interaction response. This method is a bit "smarter" than
        :meth:`create_response`. If the token is no longer valid, it sends a usual
        channel message instead of creating an interaction response.

        Parameters
        ----------
        content : :class:`str`
            message content
        embed : :class:`discord.Embed`
            message embed
        embeds : :class:`List[discord.Embed]`
            a list of up to 10 embeds to attach
        components : :class:`List[ActionRow]`
            a list of up to 5 action rows
        file : :class:`discord.File`
            if it's the first interaction reply, the file will be ignored due to API limitations.
            Everything else is the same as in :class:`discord.TextChannel.send()` method.
        files : List[:class:`discord.File`]
            same as ``file`` but for multiple files.
        hide_user_input : :class:`bool`
            if set to ``True``, user's input won't be displayed
        ephemeral : :class:`bool`
            if set to ``True``, your response will only be visible to the command author
        tts : :class:`bool`
            whether the message is text-to-speech or not
        delete_after : :class:`float`
            if specified, your reply will be deleted after ``delete_after`` seconds
        allowed_mentions : :class:`discord.AllowedMentions`
            controls the mentions being processed in this message.
        type : :class:`int` | :class:`ResponseType`
            sets the response type. If it's not specified, this method sets
            it according to ``hide_user_input``, ``content`` and ``embed`` params.
        fetch_response_message : :class:`bool`
            whether to fetch and return the response message. Defaults to ``True``.

        Raises
        ------
        ~discord.HTTPException
            sending the response failed
        ~discord.InvalidArgument
            Both ``embed`` and ``embeds`` are specified

        Returns
        -------
        message : :class:`discord.Message` | ``None``
            The response message that has been sent or ``None`` if the message is ephemeral
        """
        is_empty_message = content is None and embed is None and embeds is None
        # Which callback type is it
        if type is None:
            if is_empty_message:
                type = 1 if hide_user_input else 5
            else:
                type = 3 if hide_user_input else 4
        # Sometimes we have to use TextChannel.send() instead
        if self._sent or self.expired or type == 3:
            return await self.channel.send(
                content=content, embed=embed,
                file=file, files=files,
                tts=tts, delete_after=delete_after,
                allowed_mentions=allowed_mentions,
                components=components
            )
        # Create response
        await self.create_response(
            content=content,
            type=type,
            embed=embed,
            embeds=embeds,
            components=components,
            ephemeral=ephemeral,
            tts=tts,
            allowed_mentions=allowed_mentions
        )
        self._sent = True
        # Type-5 responses are always editable
        if type == 5:
            self.editable = True
            return None
        # Ephemeral messages aren't stored and can't be deleted or edited
        # Same for type-1 and type-2 messages
        if ephemeral or type in (1, 2):
            return None
        
        self.editable = True
        if delete_after is not None:
            self._client.loop.create_task(self.delete_after(delete_after))
        
        if fetch_response_message:
            return await self.fetch_initial_response()

    async def create_response(self, content=None, *, type=None, embed=None, embeds=None,
                                                    components=None,
                                                    ephemeral=False, tts=False,
                                                    allowed_mentions=None):
        """
        Creates an interaction response.

        Parameters
        ----------
        content : :class:`str`
            response content
        type : :class:`int` | :class:`ResponseType`
            sets the response type. See :class:`ResponseType`
        embed : :class:`discord.Embed`
            response embed
        embeds : :class:`List[discord.Embed]`
            a list of up to 10 embeds to attach
        components : :class:`List[ActionRow]`
            a list of up to 5 action rows
        ephemeral : :class:`bool`
            if set to ``True``, your response will only be visible to the command author
        tts : :class:`bool`
            whether the message is text-to-speech or not
        allowed_mentions : :class:`discord.AllowedMentions`
            controls the mentions being processed in this message.

        Raises
        ------
        ~discord.HTTPException
            sending the response failed
        ~discord.InvalidArgument
            Both ``embed`` and ``embeds`` are specified
        """
        type = type or 4
        
        data = {}
        if content is not None:
            data['content'] = str(content)
        # Embed or embeds
        if embed is not None and embeds is not None:
            raise discord.InvalidArgument("Can't pass both embed and embeds")
        
        if embed is not None:
            if not isinstance(embed, discord.Embed):
                raise discord.InvalidArgument('embed parameter must be discord.Embed')
            data['embeds'] = [embed.to_dict()]
        
        elif embeds is not None:
            if len(embeds) > 10:
                raise discord.InvalidArgument('embds parameter must be a list of up to 10 elements')
            elif not all(isinstance(embed, discord.Embed) for embed in embeds):
                raise discord.InvalidArgument('embeds parameter must be a list of discord.Embed')
            data['embeds'] = [embed.to_dict() for embed in embeds]
        
        if components is not None:
            if len(components) > 5:
                raise discord.InvalidArgument("components must be a list of up to 5 elements")
            if not all(isinstance(comp, ActionRow) for comp in components):
                raise discord.InvalidArgument("components must be a list of ActionRow")
            data["components"] = [comp.to_dict() for comp in components]
        
        # Allowed mentions
        if content or embed or embeds:
            state = self._client._connection
            if allowed_mentions is not None:
                if state.allowed_mentions is not None:
                    allowed_mentions = state.allowed_mentions.merge(allowed_mentions).to_dict()
                else:
                    allowed_mentions = allowed_mentions.to_dict()
                data['allowed_mentions'] = allowed_mentions
        # Message design
        if ephemeral:
            data["flags"] = 64
        if tts:
            data["tts"] = True
        # Final JSON formation
        _json = {"type": type}
        if len(data) > 0:
            _json["data"] = data
        # HTTP-request
        await self._client.http.request(
            Route(
                'POST', '/interactions/{interaction_id}/{token}/callback',
                interaction_id=self.id, token=self.token
            ),
            json=_json
        )

    async def edit(self, content=None, *, embed=None, embeds=None, components=None, allowed_mentions=None):
        """
        Edits the original interaction response.

        Parameters
        ----------
        content : :class:`str`
            New message content
        embed : :class:`discord.Embed`
            New message embed
        embeds : :class:`List[discord.Embed]`
            a list of up to 10 embeds of a new message
        components : :class:`List[ActionRow]`
            a list of up to 5 action rows
        allowed_mentions : :class:`discord.AllowedMentions`
            controls the mentions being processed in this message.
        
        Returns
        -------
        message : :class:`discord.Message`
            The message that was edited
        """
        if not self.editable:
            raise TypeError("There's nothing to edit or the message is ephemeral.")
        # Form JSON params
        data = {}
        if content is not None:
            data['content'] = str(content)
        # Embed or embeds
        if embed is not None and embeds is not None:
            raise discord.InvalidArgument("Can't pass both embed and embeds")
        
        if embed is not None:
            if not isinstance(embed, discord.Embed):
                raise discord.InvalidArgument('embed parameter must be discord.Embed')
            data['embeds'] = [embed.to_dict()]

        elif embeds is not None:
            if len(embeds) > 10:
                raise discord.InvalidArgument('embds parameter must be a list of up to 10 elements')
            elif not all(isinstance(embed, discord.Embed) for embed in embeds):
                raise discord.InvalidArgument('embeds parameter must be a list of discord.Embed')
            data['embeds'] = [embed.to_dict() for embed in embeds]
        # Maybe components
        if components is not None:
            if len(components) > 5:
                raise discord.InvalidArgument("components must be a list of up to 5 elements")
            if not all(isinstance(comp, ActionRow) for comp in components):
                raise discord.InvalidArgument("components must be a list of ActionRow")
            data["components"] = [comp.to_dict() for comp in components]
        # Allowed mentions
        state = self._client._connection
        if allowed_mentions is not None:
            if state.allowed_mentions is not None:
                allowed_mentions = state.allowed_mentions.merge(allowed_mentions).to_dict()
            else:
                allowed_mentions = allowed_mentions.to_dict()
            data['allowed_mentions'] = allowed_mentions
        # HTTP-response
        r = await self._client.http.request(
            Route(
                'PATCH', '/webhooks/{app_id}/{token}/messages/@original',
                app_id=self._client.user.id, token=self.token
            ),
            json=data
        )
        return discord.Message(
            state=state,
            channel=self.channel,
            data=r
        )
    
    async def delete(self):
        """
        Deletes the original interaction response.
        """
        if not self.editable:
            raise TypeError("There's nothing to delete. Send a reply first.")
        # patch
        await self._client.http.request(
            Route(
                'DELETE', '/webhooks/{app_id}/{token}/messages/@original',
                app_id=self._client.user.id, token=self.token
            )
        )
        self.editable = False
    
    async def delete_after(self, delay: float):
        await asyncio.sleep(delay)
        try:
            await self.delete()
        except:
            pass

    async def fetch_initial_response(self):
        """
        Fetches the original interaction response.
        """
        data = await self._client.http.request(
            Route(
                'GET', '/webhooks/{app_id}/{token}/messages/@original',
                app_id=self._client.user.id, token=self.token
            )
        )
        return discord.Message(
            state=self._client._connection,
            channel=self.channel,
            data=data
        )

    async def followup(self, content=None, *,   embed=None, embeds=None,
                                                file=None, files=None,
                                                tts=None, allowed_mentions=None):
        """
        Sends a followup message, which is basically a channel message
        referencing the original interaction response.

        Parameters are similar to :class:`discord.TextChannel.send()`
        """
        r = await self.webhook.send(
            content=content, tts=tts,
            file=file, files=files,
            embed=embed, embeds=embeds,
            allowed_mentions=allowed_mentions
        )
        return discord.Message(
            state=self._client._connection,
            channel=self.channel,
            data=r
        )

    send = reply

    respond = reply
