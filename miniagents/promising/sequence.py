"""
The main class in this module is `FlatSequence`. See its docstring for more information.
"""

from functools import partial
from typing import Generic, AsyncIterator, Union, Optional

from miniagents.promising.errors import FunctionNotProvidedError
from miniagents.promising.promise_typing import SequenceFlattener, IN, OUT, PromiseStreamer
from miniagents.promising.promising import StreamedPromise
from miniagents.promising.sentinels import Sentinel, DEFAULT


class FlatSequence(Generic[IN, OUT]):
    """
    TODO Oleksandr: produce a docstring for this class after you use it in the MiniAgents framework
    """

    sequence_promise: StreamedPromise[OUT, tuple[OUT, ...]]

    def __init__(
        self,
        incoming_streamer: PromiseStreamer[IN],
        flattener: Optional[SequenceFlattener[IN, OUT]] = None,
        start_asap: Union[bool, Sentinel] = DEFAULT,
        sequence_promise_class: type[StreamedPromise[OUT, tuple[OUT, ...]]] = StreamedPromise[OUT, tuple[OUT, ...]],
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

    def _flattener(self, zero_or_more_items: IN) -> AsyncIterator[OUT]:  # pylint: disable=method-hidden
        raise FunctionNotProvidedError(
            "The `flattener` function should be provided either via the constructor "
            "or by subclassing the `FlatSequence` class."
        )

    async def _streamer(self, _) -> AsyncIterator[OUT]:
        async for zero_or_more_items in self._incoming_streamer_aiter:
            async for item in self._flattener(zero_or_more_items):
                yield item

    async def _resolver(self, _) -> tuple[OUT, ...]:
        return tuple([item async for item in self.sequence_promise])  # pylint: disable=consider-using-generator
