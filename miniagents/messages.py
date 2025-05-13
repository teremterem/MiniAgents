"""
`Message` class and other classes related to messages.
"""

import traceback
import warnings
from types import TracebackType
from typing import Any, AsyncIterator, Iterable, Iterator, Optional, Union

import wrapt
from pydantic import BaseModel, ConfigDict

from miniagents.miniagent_typing import MessageTokenStreamer, MessageType
from miniagents.promising.errors import AppenderNotOpenError, PromisingContextError
from miniagents.promising.ext.frozen import Frozen, cached_privately
from miniagents.promising.promising import StreamAppender, StreamedPromise
from miniagents.promising.sentinels import NO_VALUE, Sentinel
from miniagents.promising.sequence import FlatSequence
from miniagents.utils import dict_to_message, as_single_text_promise, display_agent_trace


class Token(Frozen):
    @classmethod
    def non_metadata_fields(cls) -> tuple[str, ...]:
        return ()


class TextToken(Token):
    content: Optional[str] = None

    @classmethod
    def non_metadata_fields(cls) -> tuple[str, ...]:
        return ("content",)

    def _as_string(self) -> str:
        return self.content or ""

    def __init__(self, content: Optional[str] = None, **metadata) -> None:
        super().__init__(content=content, **metadata)


class Message(Frozen):
    @classmethod
    def token_class(cls) -> type[Token]:
        return Token

    @classmethod
    def non_metadata_fields(cls) -> tuple[str, ...]:
        return ()

    @classmethod
    def tokens_to_message(cls, tokens: Iterable[Token], **extra_fields) -> "Message":
        # This method is meant to be overridden only by message classes that support token streaming
        # Child classes that don't need token streaming don't need to implement this method
        raise TypeError(f"{cls.__name__} does not support token streaming.")

    def _message_to_tokens(self) -> tuple[Token, ...]:
        return (self.token_class()(**dict(self)),)

    @cached_privately
    def message_to_tokens(self) -> tuple[Token, ...]:
        """
        Convert this message into a tuple of tokens.

        NOTE: This method is cached. Please do not override it in subclasses. Override `_message_to_tokens` instead.
        """
        return self._message_to_tokens()

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
        start_soon: Union[bool, Sentinel] = NO_VALUE,
        message_token_streamer: Optional[MessageTokenStreamer] = None,
        **known_beforehand,
    ) -> "MessagePromise":
        """
        Create a MessagePromise object based on the Message class this method is called for and the provided
        arguments.
        """
        if message_token_streamer:
            return MessagePromise(
                start_soon=start_soon,
                message_token_streamer=message_token_streamer,
                message_class=cls,
                **known_beforehand,
            )
        return cls(**known_beforehand).as_promise

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._persist_message_event_triggered = False

    def _as_string(self) -> str:
        return f"```json\n{super()._as_string()}\n```"

    def serialize(self) -> dict[str, Any]:
        include_into_serialization, sub_messages = self._serialization_metadata
        model_dump = self.model_dump(include=include_into_serialization, mode="json")

        for path, message_or_messages in sub_messages.items():
            sub_dict = model_dump
            for path_part in path[:-1]:
                sub_dict = sub_dict[path_part]
            if isinstance(message_or_messages, Message):
                sub_dict[f"{path[-1]}__hash_key"] = message_or_messages.hash_key
            else:
                sub_dict[f"{path[-1]}__hash_keys"] = [message.hash_key for message in message_or_messages]
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


class StrictMessage(Message):
    model_config = ConfigDict(extra="forbid")


class TextMessage(Message):
    content: Optional[str] = None
    content_template: Optional[str] = None

    @classmethod
    def token_class(cls) -> type[TextToken]:
        return TextToken

    @classmethod
    def non_metadata_fields(cls) -> tuple[str, ...]:
        return ("content", "content_template")

    @classmethod
    def tokens_to_message(cls, tokens: Iterable[Token], **extra_fields) -> "TextMessage":
        return cls(
            content="".join(str(token) for token in tokens),
            **{k: v for k, v in extra_fields.items() if k not in cls.non_metadata_fields()},
        )

    @classmethod
    def promise(  # pylint: disable=arguments-differ
        cls,
        content: Optional[str] = None,
        *,
        content_template: Optional[str] = None,
        start_soon: Union[bool, Sentinel] = NO_VALUE,
        message_token_streamer: Optional[MessageTokenStreamer] = None,
        **known_beforehand,
    ) -> "MessagePromise":
        if message_token_streamer:
            if content is not None or content_template is not None:
                raise ValueError(
                    "If you provide `message_token_streamer` parameter, you cannot provide `content` or "
                    "`content_template` parameters."
                )
            return super().promise(
                content_template=content_template,
                start_soon=start_soon,
                message_token_streamer=message_token_streamer,
                **known_beforehand,
            )
        return super().promise(
            content=content,
            content_template=content_template,
            start_soon=start_soon,
            message_token_streamer=message_token_streamer,
            **known_beforehand,
        )

    def __init__(self, content: Optional[str] = None, **metadata) -> None:
        super().__init__(content=content, **metadata)

    def _as_string(self) -> str:
        if self.content_template is not None:
            return self.content_template.format(**dict(self))
        return self.content or ""


class ErrorMessage(TextMessage): ...


class MessagePromise(StreamedPromise[Token, Message]):
    """
    A promise of a message that can be streamed token by token.
    """

    known_beforehand: Frozen
    message_class: type[Message]

    def __init__(
        self,
        start_soon: Union[bool, Sentinel] = NO_VALUE,
        message_token_streamer: Optional[Union[MessageTokenStreamer, "MessageTokenAppender"]] = None,
        prefill_message: Optional[Message] = None,
        message_class: Optional[type[Message]] = None,
        **known_beforehand,
    ) -> None:
        # Validate initialization parameters
        if prefill_message is not None and (message_token_streamer is not None or known_beforehand):
            raise ValueError(
                "Cannot provide both 'prefill_message' and 'message_token_streamer'/'known_beforehand' parameters"
            )
        if prefill_message is None and message_token_streamer is None:
            raise ValueError("Either 'prefill_message' or 'message_token_streamer' parameter must be provided")

        if prefill_message:
            self.known_beforehand = prefill_message
            self.message_class = type(prefill_message)

            self._auxiliary_field_collector = None
            super().__init__(prefill_result=prefill_message, start_soon=False)
        else:
            if message_class is None:
                raise ValueError("'message_class' parameter must be provided if 'prefill_message' is not provided")
            self.known_beforehand = Frozen(**known_beforehand)
            self.message_class = message_class

            if isinstance(message_token_streamer, MessageTokenAppender):
                if not message_token_streamer.was_open:
                    # this check prevents potential deadlocks
                    raise AppenderNotOpenError(
                        "The MessageTokenAppender must be opened before it can be used. Put this statement "
                        "inside a `with MessageTokenAppender(...) as appender:` block to resolve this issue."
                    )
                self._auxiliary_field_collector = message_token_streamer.auxiliary_field_collector
            else:
                self._auxiliary_field_collector = {}

            self._amessage_token_streamer = message_token_streamer
            super().__init__(start_soon=start_soon)

    def _astreamer(self) -> AsyncIterator[Token]:
        return self._amessage_token_streamer(self._auxiliary_field_collector)

    async def _amessage_token_streamer(  # pylint: disable=method-hidden
        self, _: dict[str, Any]
    ) -> AsyncIterator[Token]:
        """
        The default implementation of the message token streamer that just yields the string representation of the
        message as a single token. This implementation is only called if the message was pre-filled. In case of real
        streaming the constructor of the class always overrides this method with an externally supplied streamer.
        """
        # The code below is executed when the message is prefilled but the client still requests to stream
        for token in self._result.message_to_tokens():
            yield token

    async def _aresolver(self) -> Message:
        """
        Resolve the message from the stream of tokens. Only called if the message was not pre-filled.
        """
        tokens = [token async for token in self]
        # NOTE: `_auxiliary_field_collector` is expected to be "fully formed" only after the stream is exhausted with
        #  the above comprehension
        return self.message_class.tokens_to_message(
            tokens, **{**self._auxiliary_field_collector, **dict(self.known_beforehand)}
        )


class MessageTokenAppender(StreamAppender[Token]):
    """
    A stream appender that appends message tokens to the message promise. It also maintains `auxiliary_field_collector`
    dictionary so message additional fields could be added to the message (if, for any reason, they cannot be delivered
    via tokens).
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._auxiliary_field_collector = {}

    @property
    def auxiliary_field_collector(self) -> dict[str, Any]:
        """
        This property protects `_auxiliary_field_collector` dictionary from being replaced completely. You should only
        modify it, not replace it.
        """
        return self._auxiliary_field_collector

    def append(self, piece: Union[Token, str, dict[str, Any]]) -> "MessageTokenAppender":
        if not isinstance(piece, Token) and isinstance(piece, BaseModel):
            piece = dict(piece)
        elif isinstance(piece, str):
            piece = TextToken(piece)

        if isinstance(piece, dict):
            if any(isinstance(piece.get(field), str) for field in TextToken.non_metadata_fields()):
                piece = TextToken(**piece)
            else:
                piece = Token(**piece)

        return super().append(piece)


class MessageSequence(FlatSequence[MessageType, MessagePromise]):
    message_appender: Optional["MessageSequenceAppender"]
    sequence_promise: "MessageSequencePromise"

    def __init__(
        self,
        appender_capture_errors: Union[bool, Sentinel] = NO_VALUE,
        start_soon: Union[bool, Sentinel] = NO_VALUE,
        errors_as_messages: Union[bool, Sentinel] = NO_VALUE,
    ) -> None:
        self.message_appender = MessageSequenceAppender(capture_errors=appender_capture_errors)

        self._errors_as_messages = errors_as_messages
        if self._errors_as_messages is NO_VALUE:
            # pylint: disable=import-outside-toplevel,cyclic-import
            from miniagents.miniagents import MiniAgents

            self._errors_as_messages = MiniAgents.get_current().errors_as_messages

        super().__init__(
            normal_streamer=self.message_appender.normal_appender,
            unordered_streamer=self.message_appender.unordered_appender,
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
            yield dict_to_message(dict(zero_or_more_items)).as_promise
        elif isinstance(zero_or_more_items, dict):
            yield dict_to_message(zero_or_more_items).as_promise
        elif isinstance(zero_or_more_items, str):
            yield TextMessage(zero_or_more_items).as_promise
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
    unordered_appender: StreamAppender[MessageType]

    def __init__(self, capture_errors: Union[bool, Sentinel] = NO_VALUE) -> None:
        self.normal_appender = StreamAppender(capture_errors=capture_errors)
        self.unordered_appender = StreamAppender(capture_errors=capture_errors)

    def append(self, piece: MessageType, out_of_order: bool = False) -> "MessageSequenceAppender":
        frozen_piece = self._freeze_if_needed(piece)
        if out_of_order:
            self.unordered_appender.append(frozen_piece)
        else:
            self.normal_appender.append(frozen_piece)
        return self

    def inject_out_of_order(self, piece: MessageType) -> "MessageSequenceAppender":
        self.append(piece, out_of_order=True)
        return self

    @classmethod
    def _freeze_if_needed(cls, zero_or_more_messages: MessageType) -> MessageType:
        if isinstance(zero_or_more_messages, (MessagePromise, Message, str, BaseException)):
            # these types are "frozen enough" as they are
            return zero_or_more_messages
        if isinstance(zero_or_more_messages, BaseModel):
            return dict_to_message(dict(zero_or_more_messages))
        if isinstance(zero_or_more_messages, dict):
            return dict_to_message(zero_or_more_messages)
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
        return self.normal_appender.was_open and self.unordered_appender.was_open

    @property
    def is_open(self) -> bool:
        return self.normal_appender.is_open and self.unordered_appender.is_open

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
        self.unordered_appender.open()
        return self

    def close(self, exc_value: Optional[BaseException] = None) -> bool:
        try:
            return self.normal_appender.close(exc_value)
        finally:
            self.unordered_appender.close()


class MessageSequencePromise(StreamedPromise[MessagePromise, tuple[Message, ...]]):
    """
    A promise of a sequence of messages that can be streamed message by message.
    """

    def as_single_text_promise(self, **kwargs) -> MessagePromise:
        """
        Convert this sequence promise into a single message promise that will contain all the messages from this
        sequence (separated by double newlines by default).
        """
        return as_single_text_promise(self, start_soon=False, **kwargs)


class SafeMessageSequencePromise(MessageSequencePromise):
    def __aiter__(self) -> AsyncIterator[MessagePromise]:
        return _SafeMessagePromiseIteratorProxy(super().__aiter__())


# pylint: disable=abstract-method,import-outside-toplevel


class _SafeMessagePromiseIteratorProxy(wrapt.ObjectProxy):
    async def __anext__(self) -> MessagePromise:
        try:
            message_promise = await self.__wrapped__.__anext__()
            return _SafeMessagePromiseProxy(message_promise)
        except StopAsyncIteration:
            raise
        except Exception as exc:  # pylint: disable=broad-except
            from miniagents.miniagents import MiniAgents

            if MiniAgents.get_current().error_tracebacks_in_messages:
                # TODO support `log_reduced_tracebacks` here as well ?
                error_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
                try:
                    error_lines.append(f"\nAgent trace:\n{display_agent_trace()}\n---\n")
                except PromisingContextError:
                    pass
                error_msg = "".join(error_lines)
            else:
                error_msg = f"{type(exc).__name__}: {exc}"

            return ErrorMessage.promise(error_msg)


class _SafeMessagePromiseProxy(wrapt.ObjectProxy):
    async def aresolve(self) -> Message:
        tokens = []
        try:
            async for token in self.__wrapped__:
                tokens.append(token)
            return await self.__wrapped__.aresolve()
        except Exception as exc:  # pylint: disable=broad-except
            from miniagents.miniagents import MiniAgents

            if MiniAgents.get_current().error_tracebacks_in_messages:
                # TODO support `log_reduced_tracebacks` here as well ?
                error_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
                try:
                    error_lines.append(f"\nAgent trace:\n{display_agent_trace()}\n---\n")
                except PromisingContextError:
                    pass
                error_msg = "".join(error_lines)
            else:
                error_msg = f"{type(exc).__name__}: {exc}"

            return ErrorMessage(f"{''.join([str(token) for token in tokens])}\n{error_msg}")

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
        except Exception as exc:  # pylint: disable=broad-except
            from miniagents.miniagents import MiniAgents

            if MiniAgents.get_current().error_tracebacks_in_messages:
                # TODO support `log_reduced_tracebacks` here as well ?
                error_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
                try:
                    error_lines.append(f"\nAgent trace:\n{display_agent_trace()}\n---\n")
                except PromisingContextError:
                    pass
                error_msg = "".join(error_lines)
            else:
                error_msg = f"{type(exc).__name__}: {exc}"

            return TextToken(f"\n{error_msg}")
