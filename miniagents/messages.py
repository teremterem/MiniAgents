"""
`Message` class and other classes related to messages.
"""

from functools import cached_property
from typing import Protocol, AsyncIterator, Any, Union, Iterable, AsyncIterable, Optional

from pydantic import BaseModel

from miniagents.promising.node import Node
from miniagents.promising.promising import StreamedPromise
from miniagents.promising.sentinels import Sentinel, DEFAULT


class Message(Node):
    """
    A message that can be sent between agents.
    """

    text: Optional[str] = None
    text_template: Optional[str] = None

    @cached_property
    def as_promise(self) -> "MessagePromise":
        """
        Convert this message into a MessagePromise object.
        """
        return MessagePromise(prefill_message=self)

    @classmethod
    def promise(
        cls,
        schedule_immediately: Union[bool, Sentinel] = DEFAULT,
        message_token_producer: "MessageTokenProducer" = None,
        **message_kwargs,
    ) -> "MessagePromise":
        """
        Create a MessagePromise object based on the Message class this method is called for and the provided
        arguments.
        """
        if message_token_producer:
            return MessagePromise(
                schedule_immediately=schedule_immediately,
                message_token_producer=message_token_producer,
                message_class=cls,
                **message_kwargs,
            )
        return cls(**message_kwargs).as_promise

    def serialize(self) -> dict[str, Any]:
        include_into_serialization, sub_message_hash_keys, _ = self._serialization_metadata
        model_dump = self.model_dump(include=include_into_serialization)
        for (path, field), hash_key_or_keys in sub_message_hash_keys.items():
            sub_dict = model_dump
            for path_part in path:
                sub_dict = sub_dict[path_part]
            sub_dict[field] = hash_key_or_keys
        return model_dump

    def _as_string(self) -> str:
        if self.text is not None:
            return self.text
        if self.text_template is not None:
            return self.text_template.format(**self.model_dump())
        return super()._as_string()

    @cached_property
    def _serialization_metadata(
        self,
    ) -> tuple[dict[str, Any], dict[tuple[tuple[str, ...], str], Union[str, tuple[str, ...]]], list["Message"]]:
        def build_serialization_metadata(
            node: Node,
        ) -> tuple[dict[str, Any], dict[tuple[tuple[str, ...], str], Union[str, tuple[str, ...]]], list[Message]]:
            include_into_serialization = {}
            sub_message_hash_keys = {}
            sub_messages = []

            for field, value in node.node_fields_and_values():
                if isinstance(value, Message):
                    sub_message_hash_keys[((), f"{field}__hash_key")] = value.hash_key
                    sub_messages.append(value)
                elif isinstance(value, Node):
                    # TODO TODO TODO Oleksandr: go into it recursively
                    include_into_serialization[field] = ...
                elif isinstance(value, tuple):
                    # TODO TODO TODO Oleksandr: go into it recursively
                    include_into_serialization[field] = ...
                else:
                    # any other (primitive) type of value will be included into serialization in its entirety
                    include_into_serialization[field] = ...

            return include_into_serialization, sub_message_hash_keys, sub_messages

        return build_serialization_metadata(self)


class MessagePromise(StreamedPromise[str, Message]):
    """
    A promise of a message that can be streamed token by token.
    """

    def __init__(
        self,
        schedule_immediately: Union[bool, Sentinel] = DEFAULT,
        message_token_producer: "MessageTokenProducer" = None,
        prefill_message: Optional[Message] = None,
        message_class: type[Message] = Message,
        **metadata_so_far,
    ) -> None:
        # TODO Oleksandr: raise an error if both ready_message and message_token_producer/metadata_so_far are not None
        #  (or both are None)
        if prefill_message:
            super().__init__(
                schedule_immediately=schedule_immediately,
                prefill_pieces=[str(prefill_message)],
                prefill_whole=prefill_message,
            )
        else:
            super().__init__(
                schedule_immediately=schedule_immediately,
                producer=self._producer,
                packager=self._packager,
            )
            self._message_token_producer = message_token_producer
            self._metadata_so_far = metadata_so_far
            self._message_class = message_class

    def _producer(self, _) -> AsyncIterator[str]:
        return self._message_token_producer(self._metadata_so_far)

    async def _packager(self, _) -> Message:
        return self._message_class(
            text="".join([token async for token in self]),
            **self._metadata_so_far,
        )

    def __aiter__(self) -> AsyncIterator[str]:
        # PyCharm fails to see that MessagePromise inherits AsyncIterable protocol from StreamedPromise,
        # hence the need to explicitly declare the __aiter__ method here
        return super().__aiter__()


class MessageSequencePromise(StreamedPromise[MessagePromise, tuple[MessagePromise, ...]]):
    """
    A promise of a sequence of messages that can be streamed message by message.
    """

    async def acollect_messages(self) -> tuple[Message, ...]:
        """
        Collect all messages from the sequence and return them as a tuple of Message objects.
        """
        # pylint: disable=consider-using-generator
        return tuple([await message_promise.acollect() async for message_promise in self])

    def __aiter__(self) -> AsyncIterator[MessagePromise]:
        # PyCharm fails to see that MessageSequencePromise inherits AsyncIterable protocol from StreamedPromise,
        # hence the need to explicitly declare the __aiter__ method here
        return super().__aiter__()


class MessageTokenProducer(Protocol):
    """
    A protocol for message piece producer functions.
    """

    def __call__(self, metadata_so_far: dict[str, Any]) -> AsyncIterator[str]: ...


# TODO Oleksandr: add documentation somewhere that explains what MessageType and SingleMessageType represent
SingleMessageType = Union[str, dict[str, Any], BaseModel, Message, MessagePromise, BaseException]
MessageType = Union[SingleMessageType, Iterable["MessageType"], AsyncIterable["MessageType"]]
