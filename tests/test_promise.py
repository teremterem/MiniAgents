"""
Tests for the `StreamedPromise` class.
"""

from typing import AsyncIterator

import pytest

from promisegraph.promise import StreamedPromise


@pytest.mark.parametrize("schedule_immediately", [False, True])
@pytest.mark.asyncio
async def test_stream_replay_iterator(schedule_immediately: bool) -> None:
    """
    Assert that when a `StreamedPromise` is iterated over multiple times, the `producer` is only called once.
    """
    producer_iterations = 0

    async def producer(_streamed_promise: StreamedPromise) -> AsyncIterator[int]:
        assert _streamed_promise is streamed_promise
        nonlocal producer_iterations
        for i in range(1, 6):
            producer_iterations += 1
            yield i

    async def packager(_streamed_promise: StreamedPromise) -> list[int]:
        assert _streamed_promise is streamed_promise
        return [piece async for piece in _streamed_promise]

    streamed_promise = StreamedPromise(producer, packager, schedule_immediately=schedule_immediately)

    assert [i async for i in streamed_promise] == [1, 2, 3, 4, 5]
    # iterate over the promise again
    assert [i async for i in streamed_promise] == [1, 2, 3, 4, 5]

    # test that the producer is not called multiple times (only 5 real iterations should happen)
    assert producer_iterations == 5


@pytest.mark.parametrize("schedule_immediately", [False, True])
@pytest.mark.asyncio
async def test_stream_replay_iterator_exception(schedule_immediately: bool) -> None:
    """
    Assert that when a `StreamedPromise` is iterated over multiple times and an exception is raised in the middle of
    the `producer` iterations, the exact same sequence of exceptions is replayed.
    """

    async def producer(_streamed_promise: StreamedPromise) -> AsyncIterator[int]:
        assert _streamed_promise is streamed_promise
        for i in range(1, 6):
            if i == 3:
                raise ValueError("Test error")
            yield i

    async def packager(_streamed_promise: StreamedPromise) -> list[int]:
        assert _streamed_promise is streamed_promise
        return [piece async for piece in _streamed_promise]

    streamed_promise = StreamedPromise(producer, packager, schedule_immediately=schedule_immediately)

    async def iterate_over_promise():
        promise_iterator = streamed_promise.__aiter__()

        assert await promise_iterator.__anext__() == 1
        assert await promise_iterator.__anext__() == 2
        with pytest.raises(ValueError):
            await promise_iterator.__anext__()
        with pytest.raises(StopAsyncIteration):
            await promise_iterator.__anext__()
        with pytest.raises(StopAsyncIteration):
            await promise_iterator.__anext__()

    await iterate_over_promise()
    # iterate over the stream again
    await iterate_over_promise()


@pytest.mark.parametrize("schedule_immediately", [False, True])
@pytest.mark.asyncio
async def test_stream_broken_producer(schedule_immediately: bool) -> None:
    """
    Assert that when a `StreamedPromise` tries to iterate over a broken producer it does not hang indefinitely, just
    raises an error and stops the stream.
    """
    producer = "not really a producer"

    async def packager(_streamed_promise: StreamedPromise) -> list[int]:
        assert _streamed_promise is streamed_promise
        return [piece async for piece in _streamed_promise]

    # noinspection PyTypeChecker
    streamed_promise = StreamedPromise(producer, packager, schedule_immediately=schedule_immediately)

    async def iterate_over_promise():
        promise_iterator = streamed_promise.__aiter__()

        with pytest.raises(TypeError):
            await promise_iterator.__anext__()
        with pytest.raises(StopAsyncIteration):
            await promise_iterator.__anext__()
        with pytest.raises(StopAsyncIteration):
            await promise_iterator.__anext__()

    await iterate_over_promise()
    # iterate over the stream again
    await iterate_over_promise()


@pytest.mark.parametrize("schedule_immediately", [False, True])
@pytest.mark.asyncio
async def test_streamed_promise_acollect(schedule_immediately: bool) -> None:
    """
    Assert that:
    - when a `StreamedPromise` is "collected" multiple times, the `packager` is only called once;
    - the exact same instance of the result object is returned from `acollect()` when it is called again.
    """
    packager_calls = 0

    async def producer(_streamed_promise: StreamedPromise) -> AsyncIterator[int]:
        assert _streamed_promise is streamed_promise
        for i in range(1, 6):
            yield i

    async def packager(_streamed_promise: StreamedPromise) -> list[int]:
        assert _streamed_promise is streamed_promise
        nonlocal packager_calls
        packager_calls += 1
        return [piece async for piece in _streamed_promise]

    streamed_promise = StreamedPromise(producer, packager, schedule_immediately=schedule_immediately)

    result1 = await streamed_promise.acollect()
    # "collect from the stream" again
    result2 = await streamed_promise.acollect()

    # test that the packager is not called multiple times
    assert packager_calls == 1

    assert result1 == [1, 2, 3, 4, 5]
    assert result2 is result1  # the promise should always return the exact same instance of the result object
