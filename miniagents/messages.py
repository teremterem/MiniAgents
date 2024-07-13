"""
`Message` class and other classes related to messages.
"""

from pprint import pformat
from typing import AsyncIterator, Any, Union, Optional, Iterator

from miniagents.miniagent_typing import MessageTokenStreamer
from miniagents.promising.errors import AppenderNotOpenError
from miniagents.promising.ext.frozen import Frozen, cached_privately
from miniagents.promising.promising import StreamedPromise, StreamAppender
from miniagents.utils import join_messages

MESSAGE_CONTENT_FIELD = "content"


class Message(Frozen):
    """
    A message that can be sent between agents.
    """

    content: Optional[str] = None
    content_template: Optional[str] = None

    @property
    @cached_privately
    def as_promise(self) -> "MessagePromise":
        """
        Convert this message into a MessagePromise object.
        """
        return MessagePromise(prefill_message=self)

    @classmethod
    def promise(
        cls,
        start_asap: Optional[bool] = None,
        message_token_streamer: Optional[MessageTokenStreamer] = None,
        **preliminary_metadata,
    ) -> "MessagePromise":
        """
        Create a MessagePromise object based on the Message class this method is called for and the provided
        arguments.
        """
        if message_token_streamer:
            return MessagePromise(
                start_asap=start_asap,
                message_token_streamer=message_token_streamer,
                message_class=cls,
                **preliminary_metadata,
            )
        return cls(**preliminary_metadata).as_promise

    def serialize(self) -> dict[str, Any]:
        include_into_serialization, sub_messages = self._serialization_metadata
        model_dump = self.model_dump(include=include_into_serialization)

        for path, message_or_messages in sub_messages.items():
            sub_dict = model_dump
            for path_part in path[:-1]:
                sub_dict = sub_dict[path_part]
            if isinstance(message_or_messages, Message):
                sub_dict[f"{path[-1]}__hash_key"] = message_or_messages.hash_key
            else:
                sub_dict[f"{path[-1]}__hash_keys"] = tuple(message.hash_key for message in message_or_messages)
        return model_dump

    def sub_messages(self) -> Iterator["Message"]:
        """
        Iterate over all sub-messages of this message, no matter how deep they are nested. This is a depth-first
        traversal.
        """
        _, sub_messages = self._serialization_metadata
        for _, message_or_messages in sub_messages.items():
            if isinstance(message_or_messages, Message):
                yield from message_or_messages.sub_messages()
                yield message_or_messages
            else:
                for message in message_or_messages:
                    yield from message.sub_messages()
                    yield message

    @property
    @cached_privately
    def _serialization_metadata(
        self,
    ) -> tuple[
        dict[Union[str, int], Any],
        dict[tuple[Union[str, int], ...], Union["Message", tuple["Message", ...]]],
    ]:
        include_into_serialization = {}
        sub_messages = {}

        def build_serialization_metadata(
            inclusion_dict: dict[Union[str, int], Any],
            node: Frozen,
            node_path: tuple[Union[str, int], ...],
        ) -> None:
            # pylint: disable=protected-access
            for field, value in node:
                if isinstance(value, Message):
                    sub_messages[(*node_path, field)] = value

                elif isinstance(value, Frozen):
                    sub_dict = {}
                    build_serialization_metadata(sub_dict, value, (*node_path, field))
                    inclusion_dict[field] = sub_dict

                elif isinstance(value, tuple):
                    if value and isinstance(value[0], Message):
                        # TODO Oleksandr: introduce a concept of MessageRef to also support "mixed" tuples (with
                        #  both Messages and other types of values mixed together)
                        sub_messages[(*node_path, field)] = value

                    else:
                        sub_dict = {}
                        for idx, sub_value in enumerate(value):
                            if isinstance(sub_value, Frozen):
                                sub_sub_dict = {}
                                build_serialization_metadata(sub_sub_dict, sub_value, (*node_path, field, idx))
                                sub_dict[idx] = sub_sub_dict
                            else:
                                sub_dict[idx] = ...
                        inclusion_dict[field] = sub_dict

                else:
                    # any other (primitive) type of value will be included into serialization in its entirety
                    inclusion_dict[field] = ...

        build_serialization_metadata(include_into_serialization, self, ())
        return include_into_serialization, sub_messages

    def _as_string(self) -> str:
        if self.content_template is not None:
            return self.content_template.format(**dict(self))
        if self.content is not None:
            return self.content
        return super()._as_string()

    def __init__(self, content: Optional[str] = None, **kwargs) -> None:
        super().__init__(content=content, **kwargs)
        self._persist_message_event_triggered = False


class MessagePromise(StreamedPromise[str, Message]):
    """
    A promise of a message that can be streamed token by token.
    """

    preliminary_metadata: Frozen

    def __init__(
        self,
        start_asap: Optional[bool] = None,
        message_token_streamer: Optional[Union[MessageTokenStreamer, "MessageTokenAppender"]] = None,
        prefill_message: Optional[Message] = None,
        message_class: type[Message] = Message,
        **preliminary_metadata,
    ) -> None:
        # TODO Oleksandr: raise an error if both ready_message and message_token_streamer/preliminary_metadata
        #  are not None (or both are None)
        if prefill_message:
            self.preliminary_metadata = prefill_message

            super().__init__(
                start_asap=start_asap,
                # TODO Oleksandr: shouldn't the prefilling of pieces be lazy ? the consumer might never need the
                #  textual representation of the message...
                prefill_pieces=[str(prefill_message)],
                prefill_result=prefill_message,
            )
        else:
            self.preliminary_metadata = Frozen(**preliminary_metadata)

            if isinstance(message_token_streamer, MessageTokenAppender):
                if not message_token_streamer.was_open:
                    # this check prevents potential deadlocks
                    raise AppenderNotOpenError(
                        "The MessageTokenAppender must be opened before it can be used. Put this statement "
                        "inside a `with MessageTokenAppender(...) as appender:` block to resolve this issue."
                    )
                self._metadata_so_far = message_token_streamer.metadata_so_far
                self._metadata_so_far.update(self.preliminary_metadata)
            else:
                self._metadata_so_far = dict(self.preliminary_metadata)

            self._message_token_streamer = message_token_streamer
            self._message_class = message_class
            super().__init__(start_asap=start_asap)

    def _streamer(self) -> AsyncIterator[str]:
        return self._message_token_streamer(self._metadata_so_far)

    async def _resolver(self) -> Message:
        content = "".join([token async for token in self])
        # `self._metadata_so_far` is "fully formed" only after the stream is exhausted with the above comprehension

        if MESSAGE_CONTENT_FIELD in self._metadata_so_far:
            raise ValueError(
                f"The `metadata_so_far` dictionary must NOT contain {MESSAGE_CONTENT_FIELD!r} "
                f"as it is meant to be resolved from the stream.\n"
                f"\n"
                f"Dictionary that was received:\n"
                f"\n"
                f"{pformat(self._metadata_so_far)}"
            )

        return self._message_class(
            content=content,
            **self._metadata_so_far,
        )


class MessageSequencePromise(StreamedPromise[MessagePromise, tuple[Message, ...]]):
    """
    A promise of a sequence of messages that can be streamed message by message.
    """

    def as_single_promise(self, **kwargs) -> MessagePromise:
        """
        Convert this sequence promise into a single message promise that will contain all the messages from this
        sequence (separated by double newlines by default).
        """
        return join_messages(self, start_asap=False, **kwargs)


class MessageTokenAppender(StreamAppender[str]):
    """
    A stream appender that appends message tokens to the message promise. It also maintains `metadata_so_far`
    dictionary so metadata can be added as tokens are appended.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._metadata_so_far = {}

    @property
    def metadata_so_far(self) -> dict[str, Any]:
        """
        This property protects `_metadata_so_far` dictionary from being replaced completely. You should only modify
        it, not replace it.
        """
        return self._metadata_so_far
