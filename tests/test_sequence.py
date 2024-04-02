"""
Tests for the `FlatSequence` class.
"""

from typing import AsyncIterator

import pytest

from miniagents.promisegraph.sequence import FlatSequence


@pytest.mark.parametrize("schedule_immediately", [False, True])
@pytest.mark.parametrize("collect_as_soon_as_possible", [False, True])
@pytest.mark.asyncio
async def test_flat_sequence(schedule_immediately: bool, collect_as_soon_as_possible: bool) -> None:
    """
    Assert that `FlatSequence` "flattens" the input sequence of (0, 1, 2, 3) into the output sequence of
    (1, 2, 2, 3, 3, 3), in accordance with the flattener function that is passed to its constructor.
    """

    async def flattener(_, number: int) -> AsyncIterator[int]:
        for _ in range(number):
            yield number

    flat_sequence = FlatSequence[int, int](
        flattener=flattener,
        schedule_immediately=schedule_immediately,
        collect_as_soon_as_possible=collect_as_soon_as_possible,
        producer_capture_errors=True,
    )
    with flat_sequence.append_producer:
        flat_sequence.append_producer.append(0)
        flat_sequence.append_producer.append(1)
        flat_sequence.append_producer.append(2)
        flat_sequence.append_producer.append(3)

    assert await flat_sequence.sequence_promise.acollect() == (1, 2, 2, 3, 3, 3)
    assert [i async for i in flat_sequence.sequence_promise] == [1, 2, 2, 3, 3, 3]
