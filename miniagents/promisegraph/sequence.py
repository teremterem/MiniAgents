"""
TODO Oleksandr
"""

from typing import Generic

from miniagents.promisegraph.promise import StreamedPromise, AppendProducer
from miniagents.promisegraph.typing import ITEM


class FlatSequence(Generic[ITEM]):
    """
    TODO Oleksandr
    """

    def __init__(
        self, schedule_immediately: bool, collect_as_soon_as_possible: bool, producer_capture_errors: bool
    ) -> None:
        self.append_producer = AppendProducer[ITEM](capture_errors=producer_capture_errors)
        self.sequence_promise = StreamedPromise[ITEM, tuple[ITEM]](
            producer=self.append_producer,
            packager=self._packager,
            schedule_immediately=schedule_immediately,
            collect_as_soon_as_possible=collect_as_soon_as_possible,
        )

    async def _packager(self, _) -> tuple[ITEM, ...]:
        return tuple(item async for item in self.sequence_promise)
