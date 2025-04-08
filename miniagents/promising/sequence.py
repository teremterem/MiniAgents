"""
The main class in this module is `FlatSequence`. See its docstring for more information.
"""

import asyncio
from functools import partial
from typing import AsyncIterator, Generic, Optional

from miniagents.promising.errors import FunctionNotProvidedError
from miniagents.promising.promise_typing import IN_co, OUT_co, PromiseStreamer, SequenceFlattener
from miniagents.promising.promising import PromisingContext, StreamedPromise


class FlatSequence(Generic[IN_co, OUT_co]):
    sequence_promise: StreamedPromise[OUT_co, tuple[OUT_co, ...]]

    def __init__(
        self,
        incoming_streamer: PromiseStreamer[IN_co],
        *,
        unordered_streamer: Optional[PromiseStreamer[IN_co]] = None,  # TODO explain what this is for in the docstring
        flattener: Optional[SequenceFlattener[IN_co, OUT_co]] = None,
        start_soon: Optional[bool] = None,
        sequence_promise_class: type[StreamedPromise[OUT_co, tuple[OUT_co, ...]]] = StreamedPromise[
            OUT_co, tuple[OUT_co, ...]
        ],
    ) -> None:
        if flattener:
            self._flattener = partial(flattener, self)

        self._promising_context = PromisingContext.get_current()
        self._start_soon = start_soon
        if self._start_soon is None:
            self._start_soon = self._promising_context.start_everything_soon_by_default

        self._queue = asyncio.Queue() if self._start_soon else None

        # # TODO why do we need this promise ? it doesn't seem to accomplish anything
        # self._input_promise = StreamedPromise(
        #     streamer=self._astreamer,
        #     resolver=lambda _: None,
        #     start_soon=False,
        # )
        # TODO should I really pass `self` here ? it is not of type `StreamedPromiseBound` ? why pass anything at all ?
        self._incoming_streamer_aiter = incoming_streamer(self)
        self._unordered_streamer_aiter = unordered_streamer(self) if unordered_streamer else None

        self.sequence_promise = sequence_promise_class(
            streamer=self._astreamer,  # self._input_promise,
            resolver=self._aresolver,
            start_soon=start_soon,
        )

    def _flattener(self, zero_or_more_items: IN_co) -> AsyncIterator[OUT_co]:  # pylint: disable=method-hidden
        raise FunctionNotProvidedError(
            "The `flattener` function should be provided either via the constructor "
            "or by subclassing the `FlatSequence` class and overriding the `_flattener` method."
        )

    async def _amerge_streams(self) -> None:
        async def _process_unordered_piece(zero_or_more_items: OUT_co) -> None:
            async for item in self._flattener(zero_or_more_items):
                self._queue.put_nowait(item)

        async def _go_over_unordered_stream() -> AsyncIterator[OUT_co]:
            async for zero_or_more_items in self._unordered_streamer_aiter:  # pylint: disable=not-an-iterable
                self._promising_context.start_soon(_process_unordered_piece(zero_or_more_items))

        if self._unordered_streamer_aiter is not None:
            self._promising_context.start_soon(_go_over_unordered_stream())

        async for zero_or_more_items in self._incoming_streamer_aiter:
            async for item in self._flattener(zero_or_more_items):
                self._queue.put_nowait(item)

    async def _astreamer(self, _) -> AsyncIterator[OUT_co]:
        # if self._start_soon:
        #     self._promising_context.start_soon(self._amerge_streams())
        #     async for item in self._queue.get():
        #         # TODO TODO TODO finish properly (separate finish sentinels for both streams)
        #         yield item
        # else:
            # since we are not in `start_soon` mode, we will just yield all the "unordered" items first
            # and the ordered items after that
            if self._unordered_streamer_aiter is not None:
                async for zero_or_more_items in self._unordered_streamer_aiter:
                    # let's use `flattener` to convert [potentially] nested sequences into a "flat" sequence
                    async for item in self._flattener(zero_or_more_items):
                        yield item
            async for zero_or_more_items in self._incoming_streamer_aiter:
                # let's use `flattener` to convert [potentially] nested sequences into a "flat" sequence
                async for item in self._flattener(zero_or_more_items):
                    yield item

    async def _aresolver(self, seq_promise: StreamedPromise[OUT_co, tuple[OUT_co, ...]]) -> tuple[OUT_co, ...]:
        # pylint: disable=consider-using-generator
        return tuple([item async for item in seq_promise])
