"""
The main class in this module is `StreamedPromise`. See its docstring for more information.
"""

import asyncio
import contextvars
from asyncio import Task
from contextvars import ContextVar
from types import TracebackType
from typing import Generic, AsyncIterator, Union, Optional, Iterable, Awaitable

from miniagents.promisegraph.errors import AppendClosedError, AppendNotOpenError
from miniagents.promisegraph.sentinels import Sentinel, NO_VALUE, FAILED, END_OF_QUEUE
from miniagents.promisegraph.typing import (
    PIECE,
    WHOLE,
    StreamedPieceProducer,
    StreamedWholePackager,
    PromiseCollectedEventHandler,
)


class Promises:
    """
    TODO TODO TODO Oleksandr
    """

    _current: ContextVar[Optional["Promises"]] = ContextVar("Promises._current", default=None)

    def __init__(
        self,
        schedule_immediately_by_default: bool = True,
        producer_capture_errors_by_default: bool = False,
        on_promise_collected: Union[PromiseCollectedEventHandler, Iterable[PromiseCollectedEventHandler]] = (),
    ) -> None:
        self.parent = self._current.get()
        self.on_promise_collected: list[PromiseCollectedEventHandler] = (
            [on_promise_collected] if callable(on_promise_collected) else list(on_promise_collected)
        )
        # TODO TODO TODO Oleksandr: this list of child tasks will be a memory leak when PromiseContext is global
        self.child_tasks: list[Task] = []

        # TODO TODO TODO Oleksandr: support in StreamedPromise and AppendProducer
        self.schedule_immediately_by_default = schedule_immediately_by_default
        self.producer_capture_errors_by_default = producer_capture_errors_by_default

        self._previous_ctx_token: Optional[contextvars.Token] = None

    @classmethod
    def get_current(cls) -> "Promises":
        """
        TODO TODO TODO Oleksandr
        """
        current = cls._current.get()
        if not current:
            raise RuntimeError(
                "No `Promises` context is currently active. Did you forget to do `async with Promises():`?"
            )
        return current

    def schedule_task(self, awaitable: Awaitable) -> Task:
        """
        TODO TODO TODO Oleksandr
        """
        task = asyncio.create_task(awaitable)
        self.child_tasks.append(task)
        return task

    def activate(self) -> "Promises":
        """
        TODO TODO TODO Oleksandr
        """
        if self._previous_ctx_token:
            raise RuntimeError("`Promises` context manager is not reentrant")
        self._previous_ctx_token = self._current.set(self)  # <- this is the context switch
        return self

    async def afinalize(self) -> None:
        """
        TODO TODO TODO Oleksandr
        """
        await asyncio.gather(
            *self.child_tasks,
            return_exceptions=True,  # this prevents waiting until the first exception and then giving up
        )
        self._current.reset(self._previous_ctx_token)
        self._previous_ctx_token = None

    async def __aenter__(self) -> "Promises":
        return self.activate()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.afinalize()


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

    # pylint: disable=too-many-instance-attributes,too-many-arguments

    def __init__(
        self,
        schedule_immediately: bool,
        producer: Optional[StreamedPieceProducer[PIECE]] = None,
        packager: Optional[StreamedWholePackager[WHOLE]] = None,
        prefill_pieces: Optional[Iterable[PIECE]] = NO_VALUE,
        prefill_whole: Optional[WHOLE] = NO_VALUE,
    ) -> None:
        # TODO Oleksandr: raise an error if both prefill_pieces/prefilled_whole and producer/packager are set
        #  (or both are not set)
        self.__producer = producer
        self.__packager = packager

        if prefill_pieces is NO_VALUE:
            self._pieces_so_far: list[Union[PIECE, BaseException]] = []
        else:
            self._pieces_so_far: list[Union[PIECE, BaseException]] = [*prefill_pieces, StopAsyncIteration()]

        if prefill_whole is NO_VALUE:
            # NO_VALUE is used because `None` is also a legitimate value for the "whole"
            self._whole: Union[WHOLE, Sentinel, BaseException] = NO_VALUE
        else:
            self._whole = prefill_whole
            self._schedule_collected_event_handlers()

        self._all_pieces_consumed = prefill_pieces is not NO_VALUE
        self._producer_lock = asyncio.Lock()
        self._packager_lock = asyncio.Lock()

        if schedule_immediately and prefill_pieces is NO_VALUE:
            # start producing pieces at the earliest task switch (put them in a queue for further consumption)
            self._queue = asyncio.Queue()
            Promises.get_current().schedule_task(self._aproduce_the_stream())
        else:
            # each piece will be produced on demand (when the first consumer iterates over it and not earlier)
            self._queue = None

        if schedule_immediately and prefill_whole is NO_VALUE:
            Promises.get_current().schedule_task(self.acollect())

        self._producer_iterator: Union[Optional[AsyncIterator[PIECE]], Sentinel] = None

    def __aiter__(self) -> AsyncIterator[PIECE]:
        """
        This allows to consume the stream piece by piece. Each new iterator returned by `__aiter__` will replay
        the stream from the beginning.
        """
        return self._StreamReplayIterator(self)

    def __call__(self, *args, **kwargs) -> AsyncIterator[PIECE]:
        """
        This enables the `StreamedPromise` to be used as a piece producer for another `StreamedPromise`, effectively
        chaining them together.
        """
        return self.__aiter__()

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
                    try:
                        self._whole = await self.__packager(self)
                    except BaseException as exc:  # pylint: disable=broad-except
                        self._whole = exc

                    self._schedule_collected_event_handlers()

        if isinstance(self._whole, BaseException):
            raise self._whole
        return self._whole

    def _schedule_collected_event_handlers(self):
        promises = Promises.get_current()
        while promises:
            for handler in promises.on_promise_collected:
                promises.schedule_task(handler(self, self._whole))
            promises = promises.parent

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
                if not callable(self._producer_iterator.__anext__):
                    raise TypeError("The producer must return an async iterator")
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


class AppendProducer(Generic[PIECE], AsyncIterator[PIECE]):
    """
    This is a special kind of `producer` that can be fed into `StreamedPromise` constructor. Objects of this class
    implement the context manager protocol and an `append()` method, which allows for passing such an object into
    `StreamedPromise` constructor while also keeping a reference to it in the outside code in order to `feed` the
    pieces into it (and, consequently, into the `StreamedPromise`) later using `append()`.
    TODO Oleksandr: explain the `capture_errors` parameter
    """

    def __init__(self, capture_errors: bool) -> None:
        self._queue = asyncio.Queue()
        self._append_open = False
        self._append_closed = False
        self._capture_errors = capture_errors

    def __enter__(self) -> "AppendProducer":
        return self.open()

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> bool:
        is_append_closed_error = isinstance(exc_value, AppendClosedError)
        if exc_value and not is_append_closed_error and self._capture_errors:
            self.append(exc_value)
        self.close()
        # if `_capture_errors` is True, then we also return True, so that the exception is not propagated outside
        # the `with` block (except if the error is an `AppendClosedError` - in this case, we do not suppress it)
        return self._capture_errors and not is_append_closed_error

    def append(self, piece: PIECE) -> "AppendProducer":
        """
        Append a `piece` to the producer. This method can only be called when the producer is open for appending (and
        also not closed yet). Consequently, the `piece` is delivered to the `StreamedPromise` that is consuming from
        this producer.
        """
        if not self._append_open:
            raise AppendNotOpenError(
                "You need to put the `append()` operation inside a `with AppendProducer()` block "
                "(or call `open()` and `close()` manually)."
            )
        if self._append_closed:
            raise AppendClosedError("The AppendProducer has already been closed for appending.")
        self._queue.put_nowait(piece)
        return self

    def open(self) -> "AppendProducer":
        """
        Open the producer for appending.

        ATTENTION! It is highly recommended to use the `with` statement instead of calling `open()` and `close()`
        manually.

        Forgetting to call `close()` or not calling it due to an exception will result in `StreamedPromise`
        (and the code that is consuming from it) waiting for more `pieces` forever.
        """
        if self._append_closed:
            raise AppendClosedError("Once closed, the AppendProducer cannot be opened again.")
        self._append_open = True
        return self

    def close(self) -> None:
        """
        Close the producer after all the pieces have been appended.

        ATTENTION! It is highly recommended to use the `with` statement instead of calling `open()` and `close()`
        manually.

        Forgetting to call `close()` or not calling it due to an exception will result in `StreamedPromise`
        (and the code that is consuming from it) waiting for more `pieces` forever.
        """
        if self._append_closed:
            return
        self._append_closed = True
        self._queue.put_nowait(END_OF_QUEUE)

    async def __anext__(self) -> PIECE:
        if self._queue is None:
            raise StopAsyncIteration()

        piece = await self._queue.get()
        if piece is END_OF_QUEUE:
            self._queue = None
            raise StopAsyncIteration()

        return piece

    def __call__(self, *args, **kwargs) -> AsyncIterator[PIECE]:
        return self
