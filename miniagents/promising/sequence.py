"""
The main class in this module is `FlatSequence`. See its docstring for more information.
"""

import asyncio
from functools import partial
from typing import AsyncIterator, Generic, Optional, Union

from miniagents.promising.errors import FunctionNotProvidedError
from miniagents.promising.promise_typing import IN_co, OUT_co, PromiseStreamer, SequenceFlattener
from miniagents.promising.promising import PromisingContext, StreamedPromise
from miniagents.promising.sentinels import END_OF_QUEUE, END_OF_UNORDERED_QUEUE, NO_VALUE, Sentinel


class FlatSequence(Generic[IN_co, OUT_co]):
    sequence_promise: StreamedPromise[OUT_co, tuple[OUT_co, ...]]

    def __init__(
        self,
        normal_streamer: PromiseStreamer[IN_co],
        *,
        # TODO explain what this streamer is for in the docstring
        unordered_streamer: Optional[PromiseStreamer[IN_co]] = None,
        flattener: Optional[SequenceFlattener[IN_co, OUT_co]] = None,
        start_soon: Union[bool, Sentinel] = NO_VALUE,
        sequence_promise_class: type[StreamedPromise[OUT_co, tuple[OUT_co, ...]]] = StreamedPromise[
            OUT_co, tuple[OUT_co, ...]
        ],
    ) -> None:
        if flattener:
            self._flattener = partial(flattener, self)

        self._promising_context = PromisingContext.get_current()
        self._start_soon = start_soon
        if self._start_soon is NO_VALUE:
            self._start_soon = self._promising_context.start_everything_soon_by_default
        del start_soon

        self._queue = asyncio.Queue()

        # # TODO why do we need this promise ? it doesn't seem to accomplish anything
        # self._input_promise = StreamedPromise(
        #     streamer=self._astreamer,
        #     resolver=lambda _: None,
        #     start_soon=False,
        # )
        # TODO should I really pass `self` here ? it is not of type `StreamedPromiseBound` ? why pass anything at all ?
        self._normal_streamer_aiter = normal_streamer(self)
        self._unordered_streamer_aiter = unordered_streamer(self) if unordered_streamer else None

        self.sequence_promise = sequence_promise_class(
            streamer=self._astreamer,  # self._input_promise,
            resolver=self._aresolver,
            start_soon=self._start_soon,
        )

    def _flattener(self, zero_or_more_items: IN_co) -> AsyncIterator[OUT_co]:  # pylint: disable=method-hidden
        raise FunctionNotProvidedError(
            "The `flattener` function should be provided either via the constructor "
            "or by subclassing the `FlatSequence` class and overriding the `_flattener` method."
        )

    async def _amerge_streams(self) -> None:
        # TODO a detailed docstring is crucial for this private method
        # TODO we might want to stop processing any more items if an exception is raised and we are not in
        #  "exceptions as messages" mode (the latter being a partially implemented feature)
        async def _process_unordered_piece(zero_or_more_items: OUT_co) -> None:
            try:
                # let's use `flattener` to convert [potentially] nested sequences into a "flat" sequence
                async for item in self._flattener(zero_or_more_items):
                    self._queue.put_nowait(item)
            except BaseException as exc:  # pylint: disable=broad-except
                self._queue.put_nowait(exc)

        async def _go_over_unordered_stream() -> None:
            try:
                subtasks = []
                async for zero_or_more_items in self._unordered_streamer_aiter:  # pylint: disable=not-an-iterable
                    subtask = self._promising_context.start_soon(_process_unordered_piece(zero_or_more_items))
                    subtasks.append(subtask)

                # let's wait for all the parallel "flattening" of unordered items before we signal that the high
                # priority stream is finished
                await self._promising_context.agather(*subtasks)
            except BaseException as exc:  # pylint: disable=broad-except
                self._queue.put_nowait(exc)
            finally:
                self._queue.put_nowait(END_OF_UNORDERED_QUEUE)

        try:
            if self._unordered_streamer_aiter is not None:
                self._promising_context.start_soon(_go_over_unordered_stream())

            async for zero_or_more_items in self._normal_streamer_aiter:
                try:
                    # let's use `flattener` to convert [potentially] nested sequences into a "flat" sequence
                    async for item in self._flattener(zero_or_more_items):
                        self._queue.put_nowait(item)
                except BaseException as exc:  # pylint: disable=broad-except
                    self._queue.put_nowait(exc)
        except BaseException as exc:  # pylint: disable=broad-except
            self._queue.put_nowait(exc)
        finally:
            self._queue.put_nowait(END_OF_QUEUE)

    async def _astreamer(self, _) -> AsyncIterator[OUT_co]:
        normal_stream_finished = self._normal_streamer_aiter is None  # will always be `False`, though
        unordered_stream_finished = self._unordered_streamer_aiter is None

        self._promising_context.start_soon(self._amerge_streams())
        while True:
            item = await self._queue.get()
            if item is END_OF_UNORDERED_QUEUE:
                unordered_stream_finished = True
            elif item is END_OF_QUEUE:
                normal_stream_finished = True
            else:
                yield item

            if normal_stream_finished and unordered_stream_finished:
                return

    async def _aresolver(self, seq_promise: StreamedPromise[OUT_co, tuple[OUT_co, ...]]) -> tuple[OUT_co, ...]:
        # pylint: disable=consider-using-generator
        return tuple([item async for item in seq_promise])
