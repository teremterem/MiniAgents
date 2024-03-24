"""
The main class in this module is `StreamedPromise`. See its docstring for more information.
"""

import asyncio
from typing import TypeVar, Generic, AsyncIterator, Union, Optional, Protocol

from promisegraph.sentinels import NO_VALUE, Sentinel, FAILED

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


class StreamedPromise(Generic[PIECE, WHOLE]):
    """
    A StreamedPromise represents a promise of a whole value that can be streamed piece by piece.

    The StreamedPromise allows for "replaying" the stream of pieces without involving the producer
    for the pieces that have already been produced. This means that multiple consumers can iterate
    over the stream independently, and each consumer will receive all the pieces from the beginning,
    even if some pieces were produced before the consumer started iterating.

    :param producer: A callable that returns an async iterator yielding the pieces of the whole value.
    :param packager: A callable that takes an async iterable of pieces and returns the whole value
                     ("packages" the pieces).
    TODO Oleksandr: explain the `schedule_immediately` parameter
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        producer: StreamedPieceProducer[PIECE],
        packager: StreamedWholePackager[WHOLE],
        schedule_immediately: bool = False,
        # TODO Oleksandr: also make it possible to supply all the pieces (as well as the whole) at once,
        #  without a producer (or a packager)
    ) -> None:
        self.__packager = packager
        self.__producer = producer

        self._pieces_so_far: list[Union[PIECE, BaseException]] = []
        # NO_VALUE is used because `None` is also a legitimate value for the "whole"
        self._whole: Union[Optional[WHOLE], Sentinel] = NO_VALUE

        self._all_pieces_consumed = False
        self._producer_lock = asyncio.Lock()
        self._packager_lock = asyncio.Lock()

        if schedule_immediately:
            # start producing pieces at the earliest task switch (put them in a queue for further consumption)
            self._queue = asyncio.Queue()
            asyncio.create_task(self._aproduce_the_stream())
        else:
            # each piece will be produced on demand (when the first consumer iterates over it and not earlier)
            self._queue = None
        self._producer_iterator: Union[Optional[AsyncIterator[PIECE]], Sentinel] = None

    def __aiter__(self) -> AsyncIterator[PIECE]:
        """
        This allows to consume the stream piece by piece. Each new iterator returned by `__aiter__` will replay
        the stream from the beginning.
        """
        return _StreamReplayIterator(self)

    async def acollect(self) -> WHOLE:
        """
        "Accumulates" all the pieces of the stream and returns the "whole" value. Will return the exact
        same object (the exact same instance) if called multiple times on the same instance of `StreamedPromise`.
        """
        # TODO Oleksandr: put a deadlock prevention mechanism in place, i. e. find a way to disallow calling
        #  `acollect()` from within the `packager` function
        if self._whole is NO_VALUE:
            async with self._packager_lock:
                if self._whole is NO_VALUE:
                    self._whole = await self.__packager(self)
        return self._whole

    async def _aproduce_the_stream(self) -> None:
        while True:
            piece = await self._aproducer_iterator_next()
            self._queue.put_nowait(piece)
            if isinstance(piece, StopAsyncIteration):
                break

    async def _aproducer_iterator_next(self) -> Union[PIECE, BaseException]:
        # pylint: disable=broad-except
        if self._producer_iterator is None:
            try:
                self._producer_iterator = self.__producer(self)
            except BaseException as exc:
                self._producer_iterator = FAILED
                return exc

        elif self._producer_iterator is FAILED:
            # we were not able to instantiate the producer iterator at all - stopping the stream
            return StopAsyncIteration()

        try:
            return await self._producer_iterator.__anext__()
        except BaseException as exc:
            # Any exception, apart from `StopAsyncIteration`, will always be stored in the `_pieces_so_far` list
            # before the `StopAsyncIteration` and will not conclude the list (in other words, `StopAsyncIteration`
            # will always conclude the `_pieces_so_far` list). This is because if you keep iterating over an
            # iterator/generator past any other exception that it might raise, it is still supposed to raise
            # `StopAsyncIteration` at the end.
            return exc


# noinspection PyProtectedMember
class _StreamReplayIterator(AsyncIterator[PIECE]):
    """
    The pieces that have already been "produced" are stored in the `_pieces_so_far` attribute of the parent
    `StreamedPromise`. The `_StreamReplayIterator` first yields the pieces from `_pieces_so_far`, and then it
    continues to retrieve new pieces from the original producer of the parent `StreamedPromise`
    (`_producer_iterator` attribute of the parent `StreamedPromise`).
    """

    def __init__(self, streamed_promise: "StreamedPromise") -> None:
        self._streamed_promise = streamed_promise
        self._index = 0

    async def __anext__(self) -> PIECE:
        if self._index < len(self._streamed_promise._pieces_so_far):
            # "replay" a piece that was produced earlier
            piece = self._streamed_promise._pieces_so_far[self._index]
        elif self._streamed_promise._all_pieces_consumed:
            # we know that `StopAsyncIteration` was stored as the last piece in the piece list
            raise self._streamed_promise._pieces_so_far[-1]
        else:
            async with self._streamed_promise._producer_lock:
                if self._index < len(self._streamed_promise._pieces_so_far):
                    piece = self._streamed_promise._pieces_so_far[self._index]
                else:
                    piece = await self._real_anext()

        self._index += 1

        if isinstance(piece, BaseException):
            raise piece
        return piece

    async def _real_anext(self) -> Union[PIECE, BaseException]:
        # pylint: disable=protected-access
        if self._streamed_promise._queue is None:
            # the stream is being produced on demand, not beforehand
            piece = await self._streamed_promise._aproducer_iterator_next()
        else:
            # the stream is being produced beforehand ("schedule immediately" option)
            piece = await self._streamed_promise._queue.get()

        if isinstance(piece, StopAsyncIteration):
            # `StopAsyncIteration` will be stored as the last piece in the piece list
            self._streamed_promise._all_pieces_consumed = True

        self._streamed_promise._pieces_so_far.append(piece)
        return piece
