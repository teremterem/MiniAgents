"""
Types for the Promising part of the library.
"""

import typing
from typing import TypeVar, AsyncIterator, Protocol, Union, Any

if typing.TYPE_CHECKING:
    from miniagents.promising.node import Node

T = TypeVar("T")
PIECE = TypeVar("PIECE")
WHOLE = TypeVar("WHOLE")
IN = TypeVar("IN")
OUT = TypeVar("OUT")
PromiseBound = TypeVar("PromiseBound", bound="Promise")
StreamedPromiseBound = TypeVar("StreamedPromiseBound", bound="StreamedPromise")
FlatSequenceBound = TypeVar("FlatSequenceBound", bound="FlatSequence")


class PromiseResolver(Protocol[T]):
    """
    TODO Oleksandr: docstring
    """

    async def __call__(self, promise: PromiseBound) -> T: ...


class PromiseStreamer(Protocol[PIECE]):
    """
    TODO Oleksandr: update this docstring ?
    A protocol for piece producers. A piece producer is a function that takes a `StreamedPromise` instance as an
    argument and returns an async iterator of pieces.
    """

    def __call__(self, streamed_promise: StreamedPromiseBound) -> AsyncIterator[PIECE]: ...


class PromiseResolvedEventHandler(Protocol):
    """
    TODO Oleksandr: update this docstring
    A protocol for StreamedPromise resolution event handlers. A promise resolution event is a function that is
    scheduled to be called after StreamedPromise.aresolve() finishes resolving the promise. "Scheduled" means
    that the function is passed to the event loop for execution without blocking the current coroutine.
    """

    async def __call__(self, promise: PromiseBound, result: Any) -> None: ...


class NodeResolvedEventHandler(Protocol):
    """
    TODO Oleksandr: docstring
    """

    async def __call__(self, promise: PromiseBound, node: "Node") -> None: ...


class SequenceFlattener(Protocol[IN, OUT]):
    """
    A protocol for sequence flatteners. A sequence flattener is a function that takes a single object of type `IN`
    and asynchronously converts it into zero or more objects of type `OUT`. In other words, it "flattens" a single
    `IN` into zero or more instances of `OUT`.
    """

    def __call__(
        self, flat_sequence: FlatSequenceBound, zero_or_more_items: Union[IN, BaseException]
    ) -> AsyncIterator[OUT]: ...
