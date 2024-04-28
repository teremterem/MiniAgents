"""
The main class in this module is `FlatSequence`. See its docstring for more information.
"""

from typing import Generic, AsyncIterator, Union

from miniagents.promising.promising import StreamedPromise
from miniagents.promising.sentinels import Sentinel, DEFAULT
from miniagents.promising.typing import SequenceFlattener, IN, OUT, StreamedPieceProducer


class FlatSequence(Generic[IN, OUT]):
    """
    TODO Oleksandr: produce a docstring for this class after you use it in the MiniAgents framework
    """

    sequence_promise: StreamedPromise[OUT, tuple[OUT, ...]]

    def __init__(
        self,
        incoming_producer: StreamedPieceProducer[IN],
        flattener: SequenceFlattener[IN, OUT],
        schedule_immediately: Union[bool, Sentinel] = DEFAULT,
        sequence_promise_class: type[StreamedPromise[OUT, tuple[OUT, ...]]] = StreamedPromise[OUT, tuple[OUT, ...]],
    ) -> None:
        self.__flattener = flattener
        self._input_promise = StreamedPromise(
            producer=self._producer,
            packager=lambda _: None,
            schedule_immediately=False,
        )
        # TODO Oleksandr: should I really pass `self` here ? it is not of type `StreamedPromiseBound`
        self._incoming_producer_iterator = incoming_producer(self)

        self.sequence_promise = sequence_promise_class(
            producer=self._input_promise,
            packager=self._packager,
            schedule_immediately=schedule_immediately,
        )

    async def _producer(self, _) -> AsyncIterator[OUT]:
        async for zero_or_more_items in self._incoming_producer_iterator:
            async for item in self.__flattener(self, zero_or_more_items):
                yield item

    async def _packager(self, _) -> tuple[OUT, ...]:
        return tuple([item async for item in self.sequence_promise])  # pylint: disable=consider-using-generator
