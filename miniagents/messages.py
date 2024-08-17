"""
`Message` class and other classes related to messages.
"""

from pprint import pformat
from typing import Any, AsyncIterator, Iterator, Optional, Union

from pydantic import BaseModel

from miniagents.miniagent_typing import MessageTokenStreamer, MessageType
from miniagents.promising.errors import AppenderNotOpenError
from miniagents.promising.ext.frozen import Frozen, cached_privately
from miniagents.promising.promise_typing import PromiseStreamer
from miniagents.promising.promising import StreamAppender, StreamedPromise
from miniagents.promising.sequence import FlatSequence
from miniagents.utils import join_messages

MESSAGE_CONTENT_FIELD = "content"
MESSAGE_CONTENT_TEMPLATE_FIELD = "content_template"


class Message(Frozen):
    """
    A message that can be sent between agents.
    TODO TODO TODO Oleksandr: split this class into two: Message and NonStrictMessage
     (regular messages wouldn't allow extra fields) ?
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
    def _serialization_metadata(self) -> tuple[
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
        return f"```json\n{super()._as_string()}\n```"

    def __init__(self, content: Optional[str] = None, **metadata) -> None:
        super().__init__(content=content, **metadata)
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

            self._metadata_so_far = None
            super().__init__(prefill_result=prefill_message, start_asap=False)
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

    async def _message_token_streamer(self, _: dict[str, Any]) -> AsyncIterator[str]:  # pylint: disable=method-hidden
        """
        The default implementation of the message token streamer that just yields the string representation of the
        message as a single token. This implementation is only called if the message was pre-filled. In case of real
        streaming the constructor of the class always overrides this method with an externally supplied streamer.
        """
        yield str(self.preliminary_metadata)

    async def _resolver(self) -> Message:
        """
        Resolve the message from the stream of tokens. Only called if the message was not pre-filled.
        """
        tokens = [token async for token in self]
        # NOTE: `_metadata_so_far` is "fully formed" only after the stream is exhausted with the above comprehension

        if MESSAGE_CONTENT_FIELD in self._metadata_so_far or MESSAGE_CONTENT_TEMPLATE_FIELD in self._metadata_so_far:
            raise ValueError(
                f"The `metadata_so_far` dictionary must NOT contain neither {MESSAGE_CONTENT_FIELD!r} nor "
                f"{MESSAGE_CONTENT_TEMPLATE_FIELD!r} keys. The value of {MESSAGE_CONTENT_FIELD!r} is meant to be "
                f"resolved from the stream.\n"
                f"\n"
                f"Dictionary that was received:\n"
                f"\n"
                f"{pformat(self._metadata_so_far)}"
            )

        return self._message_class(content="".join(tokens), **self._metadata_so_far)


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


class MessageSequence(FlatSequence[MessageType, MessagePromise]):
    """
    TODO Oleksandr: docstring
    """

    message_appender: Optional["MessageSequenceAppender"]
    sequence_promise: MessageSequencePromise

    def __init__(
        self,
        appender_capture_errors: Optional[bool] = None,
        start_asap: Optional[bool] = None,
        incoming_streamer: Optional[PromiseStreamer[MessageType]] = None,
    ) -> None:
        if incoming_streamer:
            # an external streamer is provided, so we don't create the default StreamAppender
            self.message_appender = None
        else:
            self.message_appender = MessageSequenceAppender(capture_errors=appender_capture_errors)
            incoming_streamer = self.message_appender

        super().__init__(
            incoming_streamer=incoming_streamer,
            start_asap=start_asap,
            sequence_promise_class=MessageSequencePromise,
        )

    @classmethod
    def turn_into_sequence_promise(cls, messages: MessageType) -> MessageSequencePromise:
        """
        Convert an arbitrarily nested collection of messages of various types (strings, dicts, Message objects,
        MessagePromise objects etc. - see `MessageType` definition for details) into a flat and uniform
        MessageSequencePromise object.
        """
        message_sequence = cls(
            appender_capture_errors=True,
            start_asap=False,
        )
        with message_sequence.message_appender:
            message_sequence.message_appender.append(messages)
        return message_sequence.sequence_promise

    async def _flattener(  # pylint: disable=invalid-overridden-method
        self, zero_or_more_items: MessageType
    ) -> AsyncIterator[MessagePromise]:
        if isinstance(zero_or_more_items, MessagePromise):
            yield zero_or_more_items
        elif isinstance(zero_or_more_items, Message):
            yield zero_or_more_items.as_promise
        elif isinstance(zero_or_more_items, BaseModel):
            yield Message(**dict(zero_or_more_items)).as_promise
        elif isinstance(zero_or_more_items, dict):
            yield Message(**zero_or_more_items).as_promise
        elif isinstance(zero_or_more_items, str):
            yield Message(zero_or_more_items).as_promise
        elif isinstance(zero_or_more_items, BaseException):
            raise zero_or_more_items
        elif hasattr(zero_or_more_items, "__iter__"):
            for item in zero_or_more_items:
                async for message_promise in self._flattener(item):
                    yield message_promise
        elif hasattr(zero_or_more_items, "__aiter__"):
            async for item in zero_or_more_items:
                async for message_promise in self._flattener(item):
                    yield message_promise
        else:
            raise TypeError(f"Unexpected message type: {type(zero_or_more_items)}")

    async def _resolver(self, seq_promise: MessageSequencePromise) -> tuple[Message, ...]:
        """
        Resolve all the messages in the sequence (which also includes collecting all the streamed tokens)
        and return them as a tuple of Message objects.
        """
        # first collect all the message promises
        msg_promises = [msg_promise async for msg_promise in seq_promise]
        # then resolve them all
        return tuple([await msg_promise for msg_promise in msg_promises])  # pylint: disable=consider-using-generator


class MessageSequenceAppender(StreamAppender[MessageType]):
    """
    TODO Oleksandr: docstring
    """

    def append(self, piece: MessageType) -> "MessageSequenceAppender":
        super().append(self._freeze_if_possible(piece))
        return self

    @classmethod
    def _freeze_if_possible(cls, zero_or_more_messages: MessageType) -> MessageType:
        if isinstance(zero_or_more_messages, (MessagePromise, Message, str, BaseException)):
            # these types are "frozen enough" as they are
            return zero_or_more_messages
        if isinstance(zero_or_more_messages, BaseModel):
            return Message(**dict(zero_or_more_messages))
        if isinstance(zero_or_more_messages, dict):
            return Message(**zero_or_more_messages)
        if hasattr(zero_or_more_messages, "__iter__"):
            return tuple(cls._freeze_if_possible(item) for item in zero_or_more_messages)
        if hasattr(zero_or_more_messages, "__aiter__"):
            # we do not want to consume an async iterator (and execute its underlying "tasks") prematurely,
            # hence we return it as is
            return zero_or_more_messages

        raise TypeError(f"Unexpected message type: {type(zero_or_more_messages)}")
