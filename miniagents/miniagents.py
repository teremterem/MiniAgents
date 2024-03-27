"""
Split this module into multiple modules.
"""

from typing import Protocol, AsyncIterator, Any

from miniagents.promisegraph.node import Node
from miniagents.promisegraph.promise import StreamedPromise


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
        msg_piece_producer: MessagePieceProducer,
        schedule_immediately: bool = True,
    ) -> None:
        super().__init__(producer=self._producer, packager=self._packager, schedule_immediately=schedule_immediately)
        self._msg_piece_producer = msg_piece_producer
        self._metadata_so_far: dict[str, Any] = {}

    def _producer(self, _) -> AsyncIterator[str]:
        return self._msg_piece_producer(self._metadata_so_far)

    async def _packager(self, _) -> Message:
        return Message(
            text="".join([token async for token in self]),
            **self._metadata_so_far,
        )
