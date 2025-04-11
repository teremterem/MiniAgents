"""
Types of the MiniAgents framework.
"""

import typing
from typing import Any, AsyncIterable, AsyncIterator, Iterable, Protocol, Union

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

    async def __call__(self, ctx: "InteractionContext", *args, **kwargs) -> None: ...


class MessageTokenStreamer(Protocol):
    """
    A protocol for message token streamer functions.
    """

    def __call__(self, metadata_so_far: dict[str, Any]) -> AsyncIterator[str]: ...


class PersistMessageEventHandler(Protocol):
    async def __call__(self, promise: PromiseBound, message: "Message") -> None: ...


# Type definitions for messages in the MiniAgents framework
SingleMessageType = Union[str, dict[str, Any], BaseModel, "Message", "MessagePromise", BaseException]
"""
SingleMessageType represents a single message entity that can be one of:
- A string (plain text message)
- A dictionary (structured message data)
- A Pydantic BaseModel (structured message with validation)
- A Message object (framework's message class)
- A MessagePromise (asynchronous promise for a future message)
- An Exception (for error messages)
"""

MessageType = Union[SingleMessageType, Iterable["MessageType"], AsyncIterable["MessageType"]]
"""
MessageType represents either a single message (SingleMessageType) or a collection of messages:
- A single message (any SingleMessageType)
- An iterable of messages (like a list or tuple)
- An asynchronous iterable of messages (for streaming messages)

This allows functions to handle individual messages, collections of messages, or
asynchronous streams of messages interchangeably.
"""
