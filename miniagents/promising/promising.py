"""
The main class in this module is `StreamedPromise`. See its docstring for more information.
"""

import asyncio
import contextvars
import logging
from asyncio import Task
from contextvars import ContextVar
from functools import partial
from types import TracebackType
from typing import Generic, AsyncIterator, Union, Optional, Iterable, Awaitable, Any

from miniagents.promising.errors import AppenderClosedError, AppenderNotOpenError, FunctionNotProvidedError
from miniagents.promising.promise_typing import (
    T,
    PIECE,
    WHOLE,
    PromiseStreamer,
    PromiseResolvedEventHandler,
    PromiseResolver,
)
from miniagents.promising.sentinels import Sentinel, NO_VALUE, FAILED, END_OF_QUEUE, DEFAULT

logger = logging.getLogger(__name__)


class PromisingContext:
    """
    This is the main class for managing the context of promises. It is a context manager that is used to configure
    default settings for promises and to handle the lifecycle of promises (attach `on_promise_resolved` handlers,
    ensure that all the async tasks finish before this context manager exits).
    """

    start_everything_asap_by_default: bool
    appenders_capture_errors_by_default: bool
    longer_hash_keys: bool
    log_level_for_errors: int
    on_promise_resolved_handlers: list[PromiseResolvedEventHandler]
    parent: Optional["PromisingContext"]
    child_tasks: set[Task]

    _current: ContextVar[Optional["PromisingContext"]] = ContextVar("PromisingContext._current", default=None)

    def __init__(
        self,
        start_everything_asap_by_default: bool = True,
        appenders_capture_errors_by_default: bool = False,
        longer_hash_keys: bool = False,
        log_level_for_errors: int = logging.ERROR,
        on_promise_resolved: Union[PromiseResolvedEventHandler, Iterable[PromiseResolvedEventHandler]] = (),
    ) -> None:
        self.parent = self._current.get()

        self.on_promise_resolved_handlers: list[PromiseResolvedEventHandler] = (
            [on_promise_resolved] if callable(on_promise_resolved) else [*on_promise_resolved]
        )
        self.child_tasks: set[Task] = set()

        self.start_everything_asap_by_default = start_everything_asap_by_default
        self.appenders_capture_errors_by_default = appenders_capture_errors_by_default
        self.longer_hash_keys = longer_hash_keys
        self.log_level_for_errors = log_level_for_errors

        self._previous_ctx_token: Optional[contextvars.Token] = None

    @classmethod
    def get_current(cls) -> "PromisingContext":
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

    def on_promise_resolved(self, handler: PromiseResolvedEventHandler) -> PromiseResolvedEventHandler:
        """
        Add a handler to be called after a promise is resolved.
        """
        self.on_promise_resolved_handlers.append(handler)
        return handler

    def start_asap(
        self, awaitable: Awaitable, suppress_errors: bool = True, log_level_for_errors: Optional[int] = None
    ) -> Task:
        """
        Schedule a task in the current context. "Scheduling" a task this way instead of just creating it with
        `asyncio.create_task()` allows the context to keep track of the child tasks and to wait for them to finish
        before finalizing the global context.
        """
        if log_level_for_errors is None:
            log_level_for_errors = self.log_level_for_errors

        async def awaitable_wrapper() -> Any:
            # pylint: disable=broad-except
            # noinspection PyBroadException
            try:
                return await awaitable
            except Exception:
                logger.log(
                    log_level_for_errors,
                    "AN ERROR OCCURRED IN AN ASYNC BACKGROUND TASK",
                    exc_info=True,
                )
                if not suppress_errors:
                    raise
            except BaseException:
                if not suppress_errors:
                    raise
            finally:
                self.child_tasks.remove(task)

        task = asyncio.create_task(awaitable_wrapper())
        self.child_tasks.add(task)
        return task

    def activate(self) -> "PromisingContext":
        """
        Activate the context. This is a context manager method that is used to activate the context for the duration
        of the `async with` block. Can be called as a regular method as well in cases where it is not possible to use
        the `async with` block (e.g., if a PromisingContext needs to be activated for the duration of an async webserver
        being up).
        """
        if self._previous_ctx_token:
            raise RuntimeError("PromisingContext is not reentrant")
        self._previous_ctx_token = self._current.set(self)  # <- this is the context switch
        return self

    async def aflush_tasks(self) -> None:
        """
        Wait for all the child tasks to finish. This is useful when you want to wait for all the child tasks to finish
        before proceeding with the rest of the code.
        """
        while self.child_tasks:
            await asyncio.gather(
                *self.child_tasks,
                return_exceptions=True,  # this prevents waiting until the first exception and then giving up
            )

    async def afinalize(self) -> None:
        """
        Finalize the context (wait for all the child tasks to finish and reset the context). This method is called
        automatically at the end of the `async with` block.
        """
        await self.aflush_tasks()
        self._current.reset(self._previous_ctx_token)
        self._previous_ctx_token = None

    async def __aenter__(self) -> "PromisingContext":
        return self.activate()

    async def __aexit__(self, *args, **kwargs) -> None:
        await self.afinalize()

    def __enter__(self) -> "PromisingContext":
        raise RuntimeError(f"Use `async with {type(self).__name__}()` instead of `with {type(self).__name__}`.")

    def __exit__(self, *args, **kwargs) -> None: ...


class Promise(Generic[T]):
    """
    TODO Oleksandr: docstring
    """

    def __init__(
        self,
        start_asap: Union[bool, Sentinel] = DEFAULT,
        resolver: Optional[PromiseResolver[T]] = None,
        prefill_result: Union[Optional[T], Sentinel] = NO_VALUE,
    ) -> None:
        # TODO Oleksandr: raise an error if both prefill_result and resolver are set (or both are not set)
        promising_context = PromisingContext.get_current()

        if start_asap is DEFAULT:
            start_asap = promising_context.start_everything_asap_by_default

        if resolver:
            self._resolver = partial(resolver, self)

        if prefill_result is NO_VALUE:
            # NO_VALUE is used because `None` is also a legitimate value
            self._result: Union[T, Sentinel, BaseException] = NO_VALUE
        else:
            self._result = prefill_result
            self._trigger_promise_resolved_event()

        self._resolver_lock = asyncio.Lock()

        if start_asap and prefill_result is NO_VALUE:
            promising_context.start_asap(self)

    async def _resolver(self) -> T:  # pylint: disable=method-hidden
        raise FunctionNotProvidedError(
            "The `resolver` function should be provided either via the constructor "
            "or by subclassing the `Promise` class."
        )

    async def aresolve(self) -> T:
        """
        TODO Oleksandr: docstring
        """
        # TODO Oleksandr: put a deadlock prevention mechanism in place, i. e. find a way to disallow calling
        #  `aresolve()` from within the `resolver` function
        if self._result is NO_VALUE:
            async with self._resolver_lock:
                if self._result is NO_VALUE:
                    try:
                        self._result = await self._resolver()
                    except BaseException as exc:  # pylint: disable=broad-except
                        logger.debug("An error occurred while resolving a Promise", exc_info=True)
                        self._result = exc

                    self._trigger_promise_resolved_event()

        if isinstance(self._result, BaseException):
            raise self._result
        return self._result

    def __await__(self):
        return self.aresolve().__await__()

    def _trigger_promise_resolved_event(self):
        promising_context = PromisingContext.get_current()
        while promising_context:
            for handler in promising_context.on_promise_resolved_handlers:
                promising_context.start_asap(handler(self, self._result))
            promising_context = promising_context.parent


class StreamedPromise(Promise[WHOLE], Generic[PIECE, WHOLE]):
    """
    A StreamedPromise represents a promise of a whole value that can be streamed piece by piece.

    The StreamedPromise allows for "replaying" the stream of pieces without involving the `streamer`
    function for the pieces that have already been produced. This means that multiple consumers can
    iterate over the stream independently, and each consumer will receive all the pieces from the
    beginning, even if some pieces were produced before the consumer started iterating over the
    promise.

    :param streamer: A callable that returns an async iterator yielding the pieces of the whole value.
    :param resolver: A callable that takes an async iterable of pieces and returns the whole value
                     ("packages" the pieces).
    TODO Oleksandr: explain the `start_asap` parameter
    TODO Oleksandr: this is one of the central classes of the framework, hence the docstring should be
     much more detailed
    """

    def __init__(
        self,
        streamer: Optional[PromiseStreamer[PIECE]] = None,
        prefill_pieces: Union[Optional[Iterable[PIECE]], Sentinel] = NO_VALUE,
        resolver: Optional[PromiseResolver[T]] = None,
        prefill_result: Union[Optional[T], Sentinel] = NO_VALUE,
        start_asap: Union[bool, Sentinel] = DEFAULT,
    ) -> None:
        # TODO Oleksandr: raise an error if both prefill_pieces and streamer are set (or both are not set)
        promising_context = PromisingContext.get_current()

        if start_asap is DEFAULT:
            start_asap = promising_context.start_everything_asap_by_default

        super().__init__(
            start_asap=start_asap,
            resolver=resolver,
            prefill_result=prefill_result,
        )

        if streamer:
            self._streamer = partial(streamer, self)

        if prefill_pieces is NO_VALUE:
            self._pieces_so_far: list[Union[PIECE, BaseException]] = []
        else:
            self._pieces_so_far: list[Union[PIECE, BaseException]] = [*prefill_pieces, StopAsyncIteration()]

        self._all_pieces_consumed = prefill_pieces is not NO_VALUE
        self._streamer_lock = asyncio.Lock()

        if start_asap and prefill_pieces is NO_VALUE:
            # start producing pieces at the earliest task switch (put them in a queue for further consumption)
            self._queue = asyncio.Queue()
            promising_context.start_asap(self._aconsume_the_stream())
        else:
            # each piece will be produced on demand (when the first consumer iterates over it and not earlier)
            self._queue = None

        self._streamer_aiter: Union[Optional[AsyncIterator[PIECE]], Sentinel] = None

    def _streamer(self) -> AsyncIterator[PIECE]:  # pylint: disable=method-hidden
        raise FunctionNotProvidedError(
            "The `streamer` function should be provided either via the constructor "
            "or by subclassing the `StreamedPromise` class."
        )

    def __aiter__(self) -> AsyncIterator[PIECE]:
        """
        This allows to consume the stream piece by piece. Each new iterator returned by `__aiter__` will replay
        the stream from the beginning.
        """
        return self._StreamReplayIterator(self)

    def __call__(self, *args, **kwargs) -> AsyncIterator[PIECE]:
        """
        This enables the `StreamedPromise` to be used as a piece streamer for another `StreamedPromise`, effectively
        chaining them together.
        """
        return self.__aiter__()

    async def _aconsume_the_stream(self) -> None:
        while True:
            piece = await self._streamer_aiter_anext()
            self._queue.put_nowait(piece)
            if isinstance(piece, StopAsyncIteration):
                break

    async def _streamer_aiter_anext(self) -> Union[PIECE, BaseException]:
        # pylint: disable=broad-except
        if self._streamer_aiter is None:
            try:
                self._streamer_aiter = self._streamer()
                # noinspection PyUnresolvedReferences
                if not callable(self._streamer_aiter.__anext__):
                    raise TypeError("The streamer must return an async iterator")
            except BaseException as exc:
                logger.debug("An error occurred while instantiating a streamer for a StreamedPromise", exc_info=True)
                self._streamer_aiter = FAILED
                return exc

        elif self._streamer_aiter is FAILED:
            # we were not able to instantiate the streamer iterator at all - stopping the stream
            return StopAsyncIteration()

        try:
            return await self._streamer_aiter.__anext__()
        except BaseException as exc:
            if not isinstance(exc, StopAsyncIteration):
                logger.debug(
                    'An error occurred while fetching a single "piece" of a StreamedPromise from its pieces streamer.',
                    exc_info=True,
                )
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
        continues to retrieve new pieces from the original streamer of the parent `StreamedPromise`
        (`_streamer_aiter` attribute of the parent `StreamedPromise`).
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
                async with self._streamed_promise._streamer_lock:
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
                # the stream is being produced on demand, not beforehand (`start_asap` is False)
                piece = await self._streamed_promise._streamer_aiter_anext()
            else:
                # the stream is being produced beforehand (`start_asap` is True)
                piece = await self._streamed_promise._queue.get()

            if isinstance(piece, StopAsyncIteration):
                # `StopAsyncIteration` will be stored as the last piece in the piece list
                self._streamed_promise._all_pieces_consumed = True

            self._streamed_promise._pieces_so_far.append(piece)
            return piece


class StreamAppender(AsyncIterator[PIECE], Generic[PIECE]):
    """
    This is a special kind of `streamer` that can be fed into `StreamedPromise` constructor. Objects of this class
    implement the context manager protocol and an `append()` method, which allows for passing such an object into
    `StreamedPromise` constructor while also keeping a reference to it in the outside code in order to `feed` the
    pieces into it (and, consequently, into the `StreamedPromise`) later using `append()`.
    TODO Oleksandr: explain the `capture_errors` parameter
    """

    def __init__(self, capture_errors: Union[bool, Sentinel] = DEFAULT) -> None:
        self._queue = asyncio.Queue()
        self._append_was_open = False
        self._append_closed = False
        if capture_errors is DEFAULT:
            self._capture_errors = PromisingContext.get_current().appenders_capture_errors_by_default
        else:
            self._capture_errors = capture_errors

    @property
    def was_open(self) -> bool:
        """
        Return True if the appender was ever open for appending (it doesn't matter whether it is now closed or not,
        as long as it was open ever at all).
        """
        return self._append_was_open

    def __enter__(self) -> "StreamAppender":
        return self.open()

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> bool:
        is_append_closed_error = isinstance(exc_value, AppenderClosedError)
        error_should_be_squashed = self._capture_errors and not is_append_closed_error

        if exc_value and error_should_be_squashed:
            if self._append_closed:
                logger.log(
                    PromisingContext.get_current().log_level_for_errors,
                    "A STREAM APPENDER WAS NOT ABLE TO CAPTURE THE FOLLOWING ERROR "
                    "BECAUSE APPEND WAS ALREADY CLOSED:",
                    exc_info=True,
                )
            else:
                logger.debug(
                    "An error occurred while appending pieces to a %s",
                    type(self).__name__,
                    exc_info=exc_value,
                )
                self.append(exc_value)
        self.close()

        # if `capture_errors` is True, then we also return True, so that the exception is not propagated outside
        # the `with` block (except if the error is an `AppenderClosedError` - in this case, we do not suppress it)
        return error_should_be_squashed

    async def __aenter__(self) -> "StreamAppender":
        raise RuntimeError(f"Use `with {type(self).__name__}()` instead of `async with {type(self).__name__}()`.")

    async def __aexit__(self, *args, **kwargs) -> bool: ...

    def append(self, piece: PIECE) -> "StreamAppender":
        """
        Append a `piece` to the streamer. This method can only be called when the streamer is open for appending (and
        also not closed yet). Consequently, the `piece` is delivered to the `StreamedPromise` that is consuming from
        this streamer.
        """
        if not self._append_was_open:
            raise AppenderNotOpenError(
                f"You need to put the `append()` operation inside a `with {type(self).__name__}()` block "
                "(or call `open()` and `close()` manually)."
            )
        if self._append_closed:
            raise AppenderClosedError(f"The {type(self).__name__} has already been closed for appending.")
        self._queue.put_nowait(piece)
        return self

    def open(self) -> "StreamAppender":
        """
        Open the streamer for appending.

        ATTENTION! It is highly recommended to use the `with` statement instead of calling `open()` and `close()`
        manually.

        Forgetting to call `close()` or not calling it due to an exception will result in `StreamedPromise`
        (and the code that is consuming from it) waiting for more `pieces` forever.
        """
        if self._append_closed:
            raise AppenderClosedError(f"Once closed, the {type(self).__name__} cannot be opened again.")
        self._append_was_open = True
        return self

    def close(self) -> None:
        """
        Close the streamer after all the pieces have been appended.

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
