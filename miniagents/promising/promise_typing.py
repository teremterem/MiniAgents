"""
Types of the Promising part of the library.
"""

import typing
from typing import Any, AsyncIterator, Protocol, TypeVar, Union

if typing.TYPE_CHECKING:
    from miniagents.promising.promising import Promise, StreamedPromise
    from miniagents.promising.sequence import FlatSequence

T_co = TypeVar("T_co", covariant=True)
PIECE_co = TypeVar("PIECE_co", covariant=True)
WHOLE_co = TypeVar("WHOLE_co", covariant=True)
IN_co = TypeVar("IN_co", covariant=True)
OUT_co = TypeVar("OUT_co", covariant=True)
PromiseBound = TypeVar("PromiseBound", bound="Promise")
StreamedPromiseBound = TypeVar("StreamedPromiseBound", bound="StreamedPromise")
FlatSequenceBound = TypeVar("FlatSequenceBound", bound="FlatSequence")


class PromiseResolver(Protocol[T_co]):
    """
    TODO Oleksandr: docstring
    """

    async def __call__(self, promise: PromiseBound) -> T_co: ...


class PromiseStreamer(Protocol[PIECE_co]):
    """
    TODO Oleksandr: docstring
    """

    def __call__(self, streamed_promise: StreamedPromiseBound) -> AsyncIterator[PIECE_co]: ...


class PromiseResolvedEventHandler(Protocol):
    """
    A protocol for Promise resolution event handlers. A promise resolution event handler is a function that is
    scheduled to be called after Promise.aresolve() finishes resolving the promise. "Scheduled" means that the
    function is passed to the async event loop for execution without blocking the current coroutine.
    """

    async def __call__(self, promise: PromiseBound, result: Any) -> None: ...


class SequenceFlattener(Protocol[IN_co, OUT_co]):
    """
    A protocol for sequence flatteners. A sequence flattener is a function that takes a single object of type `IN_co`
    and asynchronously converts it into zero or more objects of type `OUT_co`. In other words, it "flattens" a single
    `IN_co` into zero or more instances of `OUT_co`.
    """

    def __call__(
        self, flat_sequence: FlatSequenceBound, zero_or_more_items: Union[IN_co, BaseException]
    ) -> AsyncIterator[OUT_co]: ...
