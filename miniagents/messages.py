"""
`Message` class and other classes related to messages.
"""

import copy
from functools import cached_property
from typing import AsyncIterator, Any, Union, Optional, Iterator

from miniagents.miniagent_typing import MessageTokenStreamer
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
        start_asap: Union[bool, Sentinel] = DEFAULT,
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

    @cached_property
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
            node: Node,
            node_path: tuple[Union[str, int], ...],
        ) -> None:
            for field, value in node.node_fields_and_values():
                if isinstance(value, Message):
                    sub_messages[(*node_path, field)] = value

                elif isinstance(value, Node):
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
                            if isinstance(sub_value, Node):
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
        if self.text is not None:
            return self.text
        if self.text_template is not None:
            return self.text_template.format(**self.model_dump())
        return super()._as_string()

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._persist_message_event_triggered = False


class MessagePromise(StreamedPromise[str, Message]):
    """
    A promise of a message that can be streamed token by token.
    """

    preliminary_metadata: Node

    def __init__(
        self,
        start_asap: Union[bool, Sentinel] = DEFAULT,
        message_token_streamer: Optional[MessageTokenStreamer] = None,
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
                prefill_pieces=[str(prefill_message)],
                prefill_result=prefill_message,
            )
        else:
            self.preliminary_metadata = Node(**preliminary_metadata)
            self._metadata_so_far = copy.deepcopy(preliminary_metadata)

            self._message_token_streamer = message_token_streamer
            self._message_class = message_class
            super().__init__(start_asap=start_asap)

    def _streamer(self) -> AsyncIterator[str]:
        return self._message_token_streamer(self._metadata_so_far)

    async def _resolver(self) -> Message:
        return self._message_class(
            text="".join([token async for token in self]),
            **self._metadata_so_far,
        )

    def __aiter__(self) -> AsyncIterator[str]:
        # PyCharm fails to see that MessagePromise inherits AsyncIterable protocol from StreamedPromise,
        # hence the need to explicitly declare the __aiter__ method here
        # TODO Oleksandr: is there any other way to make PyCharm see that this class inherits AsyncIterable ?
        return super().__aiter__()


class MessageSequencePromise(StreamedPromise[MessagePromise, tuple[MessagePromise, ...]]):
    """
    A promise of a sequence of messages that can be streamed message by message.
    """

    async def aresolve_messages(self) -> tuple[Message, ...]:
        """
        Resolve all the messages in the sequence (which also includes collecting all the streamed tokens)
        and return them as a tuple of Message objects.
        """
        # pylint: disable=consider-using-generator
        return tuple([await message_promise async for message_promise in self])

    def __aiter__(self) -> AsyncIterator[MessagePromise]:
        # PyCharm fails to see that MessageSequencePromise inherits AsyncIterable protocol from StreamedPromise,
        # hence the need to explicitly declare the __aiter__ method here
        # TODO Oleksandr: is there any other way to make PyCharm see that this class inherits AsyncIterable ?
        return super().__aiter__()
