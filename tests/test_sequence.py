"""
Tests for the `FlatSequence` class.
"""

from typing import AsyncIterator

import pytest

from miniagents.promising.promising import PromisingContext, StreamAppender
from miniagents.promising.sentinels import DEFAULT
from miniagents.promising.sequence import FlatSequence


@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_flat_sequence(schedule_immediately: bool) -> None:
    """
    Assert that `FlatSequence` "flattens" the input sequence of (0, 1, 2, 3) into the output sequence of
    (1, 2, 2, 3, 3, 3), in accordance with the flattener function that is passed to its constructor.
    """

    async def flattener(_, number: int) -> AsyncIterator[int]:
        for _ in range(number):
            yield number

    async with PromisingContext():
        stream_appender = StreamAppender[int](capture_errors=True)
        flat_sequence = FlatSequence[int, int](
            incoming_producer=stream_appender,
            flattener=flattener,
            schedule_immediately=schedule_immediately,
        )
        with stream_appender:
            stream_appender.append(0)
            stream_appender.append(1)
            stream_appender.append(2)
            stream_appender.append(3)

        assert await flat_sequence.sequence_promise == (1, 2, 2, 3, 3, 3)
        assert [i async for i in flat_sequence.sequence_promise] == [1, 2, 2, 3, 3, 3]
