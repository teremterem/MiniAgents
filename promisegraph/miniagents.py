"""
TODO Oleksandr: docstring
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator

from promisegraph.node import Node
from promisegraph.promise import StreamedPromise


class Message(Node):
    """
    A message that can be sent between agents.
    """

    text: str


class MessagePromise(StreamedPromise[str, Message], ABC):
    """
    A promise of a message that can be streamed piece by piece.
    """

    def __init__(self) -> None:
        super().__init__(self._token_producer, self._message_packager, schedule_immediately=True)

    @abstractmethod
    async def _token_producer(self) -> AsyncIterator[str]:  # TODO Oleksandr: what's the correct return type ?
        """
        TODO Oleksandr: docstring
        """

    @abstractmethod
    async def _message_packager(self, _) -> Message:
        """
        TODO Oleksandr: docstring
        """
