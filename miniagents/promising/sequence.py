"""
The main class in this module is `FlatSequence`. See its docstring for more information.
"""

from functools import partial
from typing import AsyncIterator, Generic, Optional

from miniagents.promising.errors import FunctionNotProvidedError
from miniagents.promising.promise_typing import IN_co, OUT_co, PromiseStreamer, SequenceFlattener
from miniagents.promising.promising import StreamedPromise


class FlatSequence(Generic[IN_co, OUT_co]):
    """
    TODO Oleksandr: docstring
    """

    sequence_promise: StreamedPromise[OUT_co, tuple[OUT_co, ...]]

    def __init__(
        self,
        incoming_streamer: PromiseStreamer[IN_co],
        flattener: Optional[SequenceFlattener[IN_co, OUT_co]] = None,
        start_asap: Optional[bool] = None,
        sequence_promise_class: type[StreamedPromise[OUT_co, tuple[OUT_co, ...]]] = StreamedPromise[
            OUT_co, tuple[OUT_co, ...]
        ],
    ) -> None:
        if flattener:
            self._flattener = partial(flattener, self)

        self._input_promise = StreamedPromise(
            streamer=self._streamer,
            resolver=lambda _: None,
            start_asap=False,
        )
        # TODO Oleksandr: should I really pass `self` here ? it is not of type `StreamedPromiseBound`
        self._incoming_streamer_aiter = incoming_streamer(self)

        self.sequence_promise = sequence_promise_class(
            streamer=self._input_promise,
            resolver=self._resolver,
            start_asap=start_asap,
        )

    def _flattener(self, zero_or_more_items: IN_co) -> AsyncIterator[OUT_co]:  # pylint: disable=method-hidden
        # TODO Oleksandr: come up with a different method name ?
        raise FunctionNotProvidedError(
            "The `flattener` function should be provided either via the constructor "
            "or by subclassing the `FlatSequence` class."
        )

    async def _streamer(self, _) -> AsyncIterator[OUT_co]:
        async for zero_or_more_items in self._incoming_streamer_aiter:
            async for item in self._flattener(zero_or_more_items):
                yield item

    async def _resolver(self, seq_promise: StreamedPromise[OUT_co, tuple[OUT_co, ...]]) -> tuple[OUT_co, ...]:
        # pylint: disable=consider-using-generator
        return tuple([item async for item in seq_promise])
