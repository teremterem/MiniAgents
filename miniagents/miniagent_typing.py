"""
Types of the MiniAgents framework.
"""

import typing
from typing import AsyncIterator, Protocol, Union, Any, Iterable, AsyncIterable

from pydantic import BaseModel

if typing.TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from miniagents.messages import Message, MessagePromise


class MessageTokenStreamer(Protocol):
    """
    A protocol for message token streamer functions.
    """

    def __call__(self, metadata_so_far: dict[str, Any]) -> AsyncIterator[str]: ...


# TODO Oleksandr: add documentation somewhere that explains what MessageType and SingleMessageType represent
SingleMessageType = Union[str, dict[str, Any], BaseModel, "Message", "MessagePromise", BaseException]
MessageType = Union[SingleMessageType, Iterable["MessageType"], AsyncIterable["MessageType"]]
