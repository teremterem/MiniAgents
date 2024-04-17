"""
The main class in this module is `StreamedPromise`. See its docstring for more information.
"""

import asyncio
import contextvars
from asyncio import Task
from contextvars import ContextVar
from types import TracebackType
from typing import Generic, AsyncIterator, Union, Optional, Iterable, Awaitable, Any

from miniagents.promisegraph.errors import AppendClosedError, AppendNotOpenError
from miniagents.promisegraph.sentinels import Sentinel, NO_VALUE, FAILED, END_OF_QUEUE, DEFAULT
from miniagents.promisegraph.typing import (
    T,
    PIECE,
    WHOLE,
    StreamedPieceProducer,
    StreamedWholePackager,
    PromiseCollectedEventHandler,
    PromiseFulfiller,
)


class PromiseContext:
    """
    This is the main class for managing the context of promises. It is a context manager that is used to configure
    default settings for promises and to handle the lifecycle of promises (attach `on_promise_collected` handlers).
    TODO Oleksandr: explain this class in more detail
    """

    _current: ContextVar[Optional["PromiseContext"]] = ContextVar("PromiseContext._current", default=None)

    def __init__(
        self,
        schedule_immediately_by_default: bool = True,
        producer_capture_errors_by_default: bool = False,
        on_promise_collected: Union[PromiseCollectedEventHandler, Iterable[PromiseCollectedEventHandler]] = (),
    ) -> None:
        self.parent = self._current.get()
        self.on_promise_collected_handlers: list[PromiseCollectedEventHandler] = (
            [on_promise_collected] if callable(on_promise_collected) else list(on_promise_collected)
        )
        self.child_tasks: set[Task] = set()

        self.schedule_immediately_by_default = schedule_immediately_by_default
        self.producer_capture_errors_by_default = producer_capture_errors_by_default

        self._previous_ctx_token: Optional[contextvars.Token] = None

    @classmethod
    def get_current(cls) -> "PromiseContext":
        """
        Get the current context. If no context is currently active, raise an error.
        """
        current = cls._current.get()
        if not current:
            raise RuntimeError(
                f"No {cls.__name__} is currently active. Did you forget to do `async with {cls.__name__}():`?"
            )
        if not isinstance(current, cls):
            raise TypeError(
                f"You seem to have done `async with {type(current).__name__}():` (or similar), "
                f"but `async with {cls.__name__}():` is expected instead."
            )
        return current

    def on_promise_collected(self, handler: PromiseCollectedEventHandler) -> PromiseCollectedEventHandler:
        """
        Add a handler to be called after a promise is collected.
        """
        self.on_promise_collected_handlers.append(handler)
        return handler

    def schedule_task(self, awaitable: Awaitable) -> Task:
        """
        Schedule a task in the current context. "Scheduling" a task this way instead of just creating it with
        `asyncio.create_task()` allows the context to keep track of the child tasks and to wait for them to finish
        before finalizing the context.
        """

        async def awaitable_wrapper() -> Any:
            try:
                return await awaitable
                # TODO Oleksandr: memorize exceptions so they can be raised when PromiseContext is finalized ?
                #  HUGE NO! that would be a memory leak
            finally:
                self.child_tasks.remove(task)

        task = asyncio.create_task(awaitable_wrapper())
        self.child_tasks.add(task)
        return task

    def activate(self) -> "PromiseContext":
        """
        Activate the context. This is a context manager method that is used to activate the context for the duration
        of the `async with` block. Can be called as a regular method as well in cases where it is not possible to use
        the `async with` block (e.g., if a PromiseContext needs to be activated for the duration of an async webserver
        being up).
        """
        if self._previous_ctx_token:
            raise RuntimeError("PromiseContext is not reentrant")
        self._previous_ctx_token = self._current.set(self)  # <- this is the context switch
        return self

    async def afinalize(self) -> None:
        """
        Finalize the context (wait for all the child tasks to finish and reset the context). This method is called
        automatically at the end of the `async with` block.
        """
        await asyncio.gather(
            *self.child_tasks,
            return_exceptions=True,  # this prevents waiting until the first exception and then giving up
        )
        self._current.reset(self._previous_ctx_token)
        self._previous_ctx_token = None

    async def __aenter__(self) -> "PromiseContext":
        return self.activate()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.afinalize()


class Promise(Generic[T]):
    """
    TODO Oleksandr
    """

    def __init__(
        self,
        schedule_immediately: Union[bool, Sentinel] = DEFAULT,
        fulfiller: Optional[PromiseFulfiller[T]] = None,
        prefill_result: Union[Optional[T], Sentinel] = NO_VALUE,
    ) -> None:
        # TODO Oleksandr: raise an error if both prefilled_whole and packager are set (or both are not set)
        promise_context = PromiseContext.get_current()

        if schedule_immediately is DEFAULT:
            schedule_immediately = promise_context.schedule_immediately_by_default

        self.__fulfiller = fulfiller

        if prefill_result is NO_VALUE:
            # NO_VALUE is used because `None` is also a legitimate value
            self._result: Union[T, Sentinel, BaseException] = NO_VALUE
        else:
            self._result = prefill_result
            self._schedule_collected_event_handlers()

        self._fulfiller_lock = asyncio.Lock()

        if schedule_immediately and prefill_result is NO_VALUE:
            promise_context.schedule_task(self.acollect())

    async def acollect(self) -> T:
        """
        TODO Oleksandr: update this docstring
        "Accumulates" all the pieces of the stream and returns the "whole" value. Will return the exact
        same object (the exact same instance) if called multiple times on the same instance of `StreamedPromise`.
        """
        # TODO Oleksandr: put a deadlock prevention mechanism in place, i. e. find a way to disallow calling
        #  `acollect()` from within the `fulfiller` function
        if self._result is NO_VALUE:
            async with self._fulfiller_lock:
                if self._result is NO_VALUE:
                    try:
                        self._result = await self.__fulfiller(self)
                    except BaseException as exc:  # pylint: disable=broad-except
                        self._result = exc

                    self._schedule_collected_event_handlers()

        if isinstance(self._result, BaseException):
            raise self._result
        return self._result

    def _schedule_collected_event_handlers(self):
        promise_ctx = PromiseContext.get_current()
        while promise_ctx:
            for handler in promise_ctx.on_promise_collected_handlers:
                promise_ctx.schedule_task(handler(self, self._result))
            promise_ctx = promise_ctx.parent


class StreamedPromise(Generic[PIECE, WHOLE], Promise[WHOLE]):
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

    def __init__(  # pylint: disable=too-many-arguments
        self,
        schedule_immediately: Union[bool, Sentinel] = DEFAULT,
        producer: Optional[StreamedPieceProducer[PIECE]] = None,
        packager: Optional[StreamedWholePackager[WHOLE]] = None,
        prefill_pieces: Union[Optional[Iterable[PIECE]], Sentinel] = NO_VALUE,
        prefill_whole: Union[Optional[WHOLE], Sentinel] = NO_VALUE,
    ) -> None:
        # TODO Oleksandr: raise an error if both prefill_pieces and producer are set (or both are not set)
        promise_context = PromiseContext.get_current()

        if schedule_immediately is DEFAULT:
            schedule_immediately = promise_context.schedule_immediately_by_default

        super().__init__(
            schedule_immediately=schedule_immediately,
            fulfiller=packager,
            prefill_result=prefill_whole,
        )
        self.__producer = producer

        if prefill_pieces is NO_VALUE:
            self._pieces_so_far: list[Union[PIECE, BaseException]] = []
        else:
            self._pieces_so_far: list[Union[PIECE, BaseException]] = [*prefill_pieces, StopAsyncIteration()]

        self._all_pieces_consumed = prefill_pieces is not NO_VALUE
        self._producer_lock = asyncio.Lock()

        if schedule_immediately and prefill_pieces is NO_VALUE:
            # start producing pieces at the earliest task switch (put them in a queue for further consumption)
            self._queue = asyncio.Queue()
            promise_context.schedule_task(self._aproduce_the_stream())
        else:
            # each piece will be produced on demand (when the first consumer iterates over it and not earlier)
            self._queue = None

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

    def __init__(self, capture_errors: Union[bool, Sentinel] = DEFAULT) -> None:
        self._queue = asyncio.Queue()
        self._append_open = False
        self._append_closed = False
        if capture_errors is DEFAULT:
            self._capture_errors = PromiseContext.get_current().producer_capture_errors_by_default
        else:
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
