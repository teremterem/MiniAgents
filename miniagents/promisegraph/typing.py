"""
Types for the PromiseGraph part of the library.
"""

from typing import TypeVar, AsyncIterator, Protocol

PIECE = TypeVar("PIECE")
WHOLE = TypeVar("WHOLE")
StreamedPromiseBound = TypeVar("StreamedPromiseBound", bound="StreamedPromise")


class StreamedPieceProducer(Protocol[PIECE]):
    """
    A protocol for piece producers. A piece producer is a function that takes a `StreamedPromise` instance
    as an argument and returns an async iterator of pieces.
    """

    def __call__(self, streamed_promise: StreamedPromiseBound) -> AsyncIterator[PIECE]: ...


class StreamedWholePackager(Protocol[WHOLE]):
    """
    A protocol for packagers of the whole value. A whole packager is a function that takes a `StreamedPromise`
    instance as an argument and returns the whole value.
    """

    async def __call__(self, streamed_promise: StreamedPromiseBound) -> WHOLE: ...
