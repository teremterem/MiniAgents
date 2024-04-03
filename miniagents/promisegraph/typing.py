"""
Types for the PromiseGraph part of the library.
"""

from typing import TypeVar, AsyncIterator, Protocol, Union

PIECE = TypeVar("PIECE")
WHOLE = TypeVar("WHOLE")
IN = TypeVar("IN")
OUT = TypeVar("OUT")
StreamedPromiseBound = TypeVar("StreamedPromiseBound", bound="StreamedPromise")
FlatSequenceBound = TypeVar("FlatSequenceBound", bound="FlatSequence")


class StreamedPieceProducer(Protocol[PIECE]):
    """
    A protocol for piece producers. A piece producer is a function that takes a `StreamedPromise` instance as an
    argument and returns an async iterator of pieces.
    """

    def __call__(self, streamed_promise: StreamedPromiseBound) -> AsyncIterator[PIECE]: ...


class StreamedWholePackager(Protocol[WHOLE]):
    """
    A protocol for packagers of the whole value. A whole packager is a function that takes a `StreamedPromise`
    instance as an argument and returns the whole value.
    """

    async def __call__(self, streamed_promise: StreamedPromiseBound) -> WHOLE: ...


class SequenceFlattener(Protocol[IN, OUT]):
    """
    A protocol for sequence flatteners. A sequence flattener is a function that takes a single object of type `IN`
    and asynchronously converts it into zero or more objects of type `OUT`. In other words, it "flattens" a single
    `IN` into zero or more instances of `OUT`.
    """

    def __call__(
        self, flat_sequence: FlatSequenceBound, zero_or_more_items: Union[IN, BaseException]
    ) -> AsyncIterator[OUT]: ...
