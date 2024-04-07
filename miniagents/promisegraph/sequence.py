"""
The main class in this module is `FlatSequence`. See its docstring for more information.
"""

from typing import Generic, AsyncIterator

from miniagents.promisegraph.promise import StreamedPromise, AppendProducer
from miniagents.promisegraph.typing import SequenceFlattener, IN, OUT


class FlatSequence(Generic[IN, OUT]):
    """
    TODO Oleksandr: produce a docstring for this class after you use it in the MiniAgents framework
    """

    append_producer: AppendProducer[IN]
    sequence_promise: StreamedPromise[OUT, tuple[OUT, ...]]

    def __init__(
        self,
        flattener: SequenceFlattener[IN, OUT],
        schedule_immediately: bool,
        producer_capture_errors: bool,
    ) -> None:
        self.__flattener = flattener
        self._input_promise = StreamedPromise(
            producer=self._producer,
            packager=lambda _: None,
            schedule_immediately=False,
        )

        self.append_producer = AppendProducer(capture_errors=producer_capture_errors)
        self.sequence_promise = StreamedPromise(
            producer=self._input_promise,
            packager=self._packager,
            schedule_immediately=schedule_immediately,
        )

    async def _producer(self, _) -> AsyncIterator[OUT]:
        async for zero_or_more_items in self.append_producer:
            async for item in self.__flattener(self, zero_or_more_items):
                yield item

    async def _packager(self, _) -> tuple[OUT, ...]:
        return tuple([item async for item in self.sequence_promise])  # pylint: disable=consider-using-generator
