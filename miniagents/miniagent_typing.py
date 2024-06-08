"""
Types of the MiniAgents framework.
"""

import typing
from typing import AsyncIterator, Protocol, Union, Any, Iterable, AsyncIterable

from pydantic import BaseModel

from miniagents.promising.promise_typing import PromiseBound

if typing.TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from miniagents.messages import Message, MessagePromise
    from miniagents.miniagents import InteractionContext


class AgentFunction(Protocol):
    """
    A protocol for agent functions.
    """

    async def __call__(self, ctx: "InteractionContext", **kwargs) -> None: ...


class MessageTokenStreamer(Protocol):
    """
    A protocol for message token streamer functions.
    """

    def __call__(self, metadata_so_far: dict[str, Any]) -> AsyncIterator[str]: ...


class PersistMessageEventHandler(Protocol):
    """
    TODO Oleksandr: docstring
    """

    async def __call__(self, promise: PromiseBound, message: "Message") -> None: ...


# TODO Oleksandr: add documentation somewhere that explains what MessageType and SingleMessageType represent
SingleMessageType = Union[str, dict[str, Any], BaseModel, "Message", "MessagePromise", BaseException]
MessageType = Union[SingleMessageType, Iterable["MessageType"], AsyncIterable["MessageType"]]
