"""
Split this module into multiple modules.
"""

from typing import Protocol, AsyncIterator, Any, Union, Iterable, AsyncIterable, Optional

from miniagents.promisegraph.node import Node
from miniagents.promisegraph.promise import StreamedPromise
from miniagents.promisegraph.sequence import FlatSequence


class Message(Node):
    """
    A message that can be sent between agents.
    """

    text: str


class MessagePieceProducer(Protocol):
    """
    A protocol for message piece producer functions.
    """

    def __call__(self, metadata_so_far: dict[str, Any]) -> AsyncIterator[str]: ...


class MessagePromise(StreamedPromise[str, Message]):
    """
    A promise of a message that can be streamed token by token.
    """

    def __init__(
        self,
        schedule_immediately: bool = True,
        collect_as_soon_as_possible: bool = True,
        message_piece_producer: MessagePieceProducer = None,
        ready_message: Optional[Message] = None,
    ) -> None:
        self._ready_message = ready_message
        super().__init__(
            producer=self._producer,
            packager=self._packager,
            schedule_immediately=schedule_immediately,
            collect_as_soon_as_possible=collect_as_soon_as_possible,
        )
        self._message_piece_producer = message_piece_producer
        self._metadata_so_far: dict[str, Any] = {}

    def _producer(self, _) -> AsyncIterator[str]:
        if self._ready_message:
            # TODO TODO TODO Oleksandr: support this scenario one way or another
            # yield from self._ready_message.text
            pass
        return self._message_piece_producer(self._metadata_so_far)

    async def _packager(self, _) -> Message:
        if self._ready_message:
            return self._ready_message
        return Message(
            text="".join([token async for token in self]),
            **self._metadata_so_far,
        )


# TODO Oleksandr: add documentation somewhere that explains what MessageType and SingleMessageType represent
SingleMessageType = Union[str, dict[str, Any], Message, MessagePromise, BaseException]
MessageType = Union[SingleMessageType, Iterable["MessageType"], AsyncIterable["MessageType"]]


class MessageSequence(FlatSequence[MessageType, MessagePromise]):
    """
    TODO TODO TODO Oleksandr
    """

    def __init__(
        self,
        producer_capture_errors: bool,
        schedule_immediately: bool = True,
        collect_as_soon_as_possible: bool = False,
    ) -> None:
        self._schedule_immediately = schedule_immediately
        self._collect_as_soon_as_possible = collect_as_soon_as_possible
        super().__init__(
            flattener=self._flattener,
            schedule_immediately=schedule_immediately,
            collect_as_soon_as_possible=collect_as_soon_as_possible,
            producer_capture_errors=producer_capture_errors,
        )

    @staticmethod
    async def _flattener(_, zero_or_more_items: MessageType) -> AsyncIterator[MessagePromise]:
        if isinstance(zero_or_more_items, MessagePromise):
            yield zero_or_more_items
        elif isinstance(zero_or_more_items, Message):
            yield MessagePromise(ready_message=zero_or_more_items)
        elif isinstance(zero_or_more_items, str):
            yield MessagePromise(ready_message=Message(text=zero_or_more_items))
        elif isinstance(zero_or_more_items, dict):
            yield MessagePromise(ready_message=Message(**zero_or_more_items))
        elif isinstance(zero_or_more_items, BaseException):
            # TODO TODO TODO Oleksandr: exceptions are raised from promises -
            #  introduce a flag to just pass them through ?
            pass
        elif hasattr(zero_or_more_items, "__iter__"):
            for item in zero_or_more_items:
                async for message_promise in MessageSequence._flattener(None, item):
                    yield message_promise
        elif hasattr(zero_or_more_items, "__aiter__"):
            async for item in zero_or_more_items:
                async for message_promise in MessageSequence._flattener(None, item):
                    yield message_promise
        else:
            raise TypeError(f"unexpected message type: {type(zero_or_more_items)}")
