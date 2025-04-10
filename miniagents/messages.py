"""
`Message` class and other classes related to messages.
"""

import warnings
from pprint import pformat
from types import TracebackType
from typing import Any, AsyncIterator, Iterator, Optional, Union

import wrapt
from pydantic import BaseModel

from miniagents.miniagent_typing import MessageTokenStreamer, MessageType
from miniagents.promising.errors import AppenderNotOpenError
from miniagents.promising.ext.frozen import Frozen, cached_privately
from miniagents.promising.promising import StreamAppender, StreamedPromise
from miniagents.promising.sequence import FlatSequence
from miniagents.utils import join_messages

MESSAGE_CONTENT_FIELD = "content"
MESSAGE_CONTENT_TEMPLATE_FIELD = "content_template"


class Message(Frozen):
    """
    A message that can be sent between agents.
    """

    # TODO split this class into two: Message and NonStrictMessage
    #  (with NonStrictMessage allowing extra fields) ?
    #  (is it to reduce confusion as to whether to expect extra fields in a message or not ?)

    content: Optional[str] = None
    content_template: Optional[str] = None

    # # TODO finish "error to message" feature
    # contains_error: bool = False
    # error_message: Optional[str] = None
    # error_class: Optional[str] = None
    # error_traceback: Optional[str] = None

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
        content: Optional[str] = None,
        start_soon: Optional[bool] = None,
        message_token_streamer: Optional[MessageTokenStreamer] = None,
        **preliminary_metadata,
    ) -> "MessagePromise":
        """
        Create a MessagePromise object based on the Message class this method is called for and the provided
        arguments.
        """
        if message_token_streamer:
            if content is not None:
                raise ValueError("The `content` argument must be None if `message_token_streamer` is provided.")
            return MessagePromise(
                start_soon=start_soon,
                message_token_streamer=message_token_streamer,
                message_class=cls,
                **preliminary_metadata,
            )
        return cls(content=content, **preliminary_metadata).as_promise

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
                        # TODO introduce a concept of MessageRef to also support "mixed" tuples (with
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
    # TODO use Token object instead of str and allow appending empty text tokens too, for simplicity
    """
    A promise of a message that can be streamed token by token.
    """

    preliminary_metadata: Frozen
    message_class: type[Message]

    def __init__(
        self,
        start_soon: Optional[bool] = None,
        message_token_streamer: Optional[Union[MessageTokenStreamer, "MessageTokenAppender"]] = None,
        prefill_message: Optional[Message] = None,
        message_class: type[Message] = Message,
        **preliminary_metadata,
    ) -> None:
        # Validate initialization parameters
        if prefill_message is not None and (message_token_streamer is not None or preliminary_metadata):
            raise ValueError(
                "Cannot provide both 'prefill_message' and 'message_token_streamer'/'preliminary_metadata' parameters"
            )
        if prefill_message is None and message_token_streamer is None:
            raise ValueError("Either 'prefill_message' or 'message_token_streamer' parameter must be provided")

        if prefill_message:
            self.preliminary_metadata = prefill_message
            self.message_class = type(prefill_message)

            self._metadata_so_far = None
            super().__init__(prefill_result=prefill_message, start_soon=False)
        else:
            self.preliminary_metadata = Frozen(**preliminary_metadata)
            self.message_class = message_class

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

            self._amessage_token_streamer = message_token_streamer
            super().__init__(start_soon=start_soon)

    def _astreamer(self) -> AsyncIterator[str]:
        return self._amessage_token_streamer(self._metadata_so_far)

    async def _amessage_token_streamer(self, _: dict[str, Any]) -> AsyncIterator[str]:  # pylint: disable=method-hidden
        """
        The default implementation of the message token streamer that just yields the string representation of the
        message as a single token. This implementation is only called if the message was pre-filled. In case of real
        streaming the constructor of the class always overrides this method with an externally supplied streamer.
        """
        yield str(self.preliminary_metadata)

    async def _aresolver(self) -> Message:
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

        return self.message_class(content="".join(tokens), **self._metadata_so_far)


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
    message_appender: Optional["MessageSequenceAppender"]
    sequence_promise: "MessageSequencePromise"

    def __init__(
        self,
        appender_capture_errors: Optional[bool] = None,
        start_soon: Optional[bool] = None,
        errors_as_messages: bool = None,  # TODO finish "error to message" feature
    ) -> None:
        self.message_appender = MessageSequenceAppender(capture_errors=appender_capture_errors)

        self._errors_as_messages = errors_as_messages
        if self._errors_as_messages is None:
            # pylint: disable=import-outside-toplevel,cyclic-import
            from miniagents.miniagents import MiniAgents

            self._errors_as_messages = MiniAgents.get_current().errors_as_messages

        super().__init__(
            normal_streamer=self.message_appender.normal_appender,
            high_priority_streamer=self.message_appender.high_priority_appender,
            start_soon=start_soon,
            sequence_promise_class=SafeMessageSequencePromise if self._errors_as_messages else MessageSequencePromise,
        )

    @classmethod
    def turn_into_sequence_promise(cls, messages: MessageType) -> "MessageSequencePromise":
        """
        Convert an arbitrarily nested collection of messages of various types (strings, dicts, Message objects,
        MessagePromise objects etc. - see `MessageType` definition for details) into a flat and uniform
        MessageSequencePromise object.
        """
        if isinstance(messages, MessageSequencePromise):
            return messages

        message_sequence = cls(
            appender_capture_errors=True,
            start_soon=False,
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

    async def _aresolver(self, seq_promise: "MessageSequencePromise") -> tuple[Message, ...]:
        """
        Resolve all the messages in the sequence (which also includes collecting all the streamed tokens)
        and return them as a tuple of Message objects.
        """
        # first collect all the message promises
        msg_promises = [msg_promise async for msg_promise in seq_promise]
        # then resolve them all
        return tuple([await msg_promise for msg_promise in msg_promises])  # pylint: disable=consider-using-generator


class MessageSequenceAppender:
    normal_appender: StreamAppender[MessageType]
    high_priority_appender: StreamAppender[MessageType]

    def __init__(self, capture_errors: Optional[bool] = None) -> None:
        self.normal_appender = StreamAppender(capture_errors=capture_errors)
        self.high_priority_appender = StreamAppender(capture_errors=capture_errors)

    def append(self, piece: MessageType, inject_as_urgent: bool = False) -> "MessageSequenceAppender":
        frozen_piece = self._freeze_if_needed(piece)
        if inject_as_urgent:
            self.high_priority_appender.append(frozen_piece)
        else:
            self.normal_appender.append(frozen_piece)
        return self

    def inject_as_urgent(self, piece: MessageType) -> "MessageSequenceAppender":
        self.append(piece, inject_as_urgent=True)
        return self

    @classmethod
    def _freeze_if_needed(cls, zero_or_more_messages: MessageType) -> MessageType:
        if isinstance(zero_or_more_messages, (MessagePromise, Message, str, BaseException)):
            # these types are "frozen enough" as they are
            return zero_or_more_messages
        if isinstance(zero_or_more_messages, BaseModel):
            return Message(**dict(zero_or_more_messages))
        if isinstance(zero_or_more_messages, dict):
            return Message(**zero_or_more_messages)
        if hasattr(zero_or_more_messages, "__iter__"):
            return tuple(cls._freeze_if_needed(item) for item in zero_or_more_messages)
        if hasattr(zero_or_more_messages, "__aiter__"):
            # we do not want to consume an async iterator (and execute its underlying "tasks") prematurely,
            # hence we return it as is
            if not isinstance(zero_or_more_messages, StreamedPromise):
                warnings.warn(
                    "An async iterator is being passed to a message sequence and will not be consumed immediately.",
                    # TODO explain in the message why this might be a problem ?
                    UserWarning,
                    stacklevel=3,
                )
            return zero_or_more_messages

        raise TypeError(f"Unexpected message type: {type(zero_or_more_messages)}")

    @property
    def was_open(self) -> bool:
        return self.normal_appender.was_open and self.high_priority_appender.was_open

    @property
    def is_open(self) -> bool:
        return self.normal_appender.is_open and self.high_priority_appender.is_open

    def __enter__(self) -> "MessageSequenceAppender":
        return self.open()

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        exc_traceback: Optional[TracebackType],
    ) -> bool:
        return self.close(exc_value)

    async def __aenter__(self) -> "MessageSequenceAppender":
        raise RuntimeError(f"Use `with {type(self).__name__}()` instead of `async with {type(self).__name__}()`.")

    async def __aexit__(self, *args, **kwargs) -> bool: ...

    def open(self) -> "MessageSequenceAppender":
        self.normal_appender.open()
        self.high_priority_appender.open()
        return self

    def close(self, exc_value: Optional[BaseException] = None) -> bool:
        try:
            return self.normal_appender.close(exc_value)
        finally:
            self.high_priority_appender.close()


class MessageSequencePromise(StreamedPromise[MessagePromise, tuple[Message, ...]]):
    """
    A promise of a sequence of messages that can be streamed message by message.
    """

    def as_single_promise(self, **kwargs) -> MessagePromise:
        """
        Convert this sequence promise into a single message promise that will contain all the messages from this
        sequence (separated by double newlines by default).
        """
        return join_messages(self, start_soon=False, **kwargs)


class SafeMessageSequencePromise(MessageSequencePromise):
    def __aiter__(self) -> AsyncIterator[MessagePromise]:
        return _SafeMessagePromiseIteratorProxy(super().__aiter__())


# pylint: disable=abstract-method


class _SafeMessagePromiseIteratorProxy(wrapt.ObjectProxy):
    async def __anext__(self) -> MessagePromise:
        try:
            message_promise = await self.__wrapped__.__anext__()
            return _SafeMessagePromiseProxy(message_promise)
        except StopAsyncIteration:
            raise
        except Exception as exc:  # pylint: disable=broad-except  # TODO finish "error to message" feature
            return Message.promise(f"{type(exc).__name__}: {str(exc)}", is_error=True)


class _SafeMessagePromiseProxy(wrapt.ObjectProxy):
    async def aresolve(self) -> Message:
        tokens = []
        try:
            async for token in self.__wrapped__:
                tokens.append(token)
            return await self.__wrapped__.aresolve()
        except Exception as exc:  # pylint: disable=broad-except  # TODO finish "error to message" feature
            return Message(f"{''.join(tokens)}\n{type(exc).__name__}: {str(exc)}", is_error=True)

    def __await__(self):
        return self.aresolve().__await__()

    def __aiter__(self):
        return _SafeMessageTokenIteratorProxy(self.__wrapped__.__aiter__())


class _SafeMessageTokenIteratorProxy(wrapt.ObjectProxy):
    async def __anext__(self) -> str:
        try:
            return await self.__wrapped__.__anext__()
        except StopAsyncIteration:
            raise
        except Exception as exc:  # pylint: disable=broad-except  # TODO finish "error to message" feature
            return f"\n{type(exc).__name__}: {str(exc)}"
