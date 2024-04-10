"""
Tests for the `StreamedPromise` class.
"""

from typing import AsyncIterator

import pytest

from miniagents.promisegraph.promise import StreamedPromise, AppendProducer, PromiseContext
from miniagents.promisegraph.sentinels import DEFAULT


@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_stream_replay_iterator(schedule_immediately: bool) -> None:
    """
    Assert that when a `StreamedPromise` is iterated over multiple times, the `producer` is only called once.
    """
    producer_iterations = 0

    async def producer(_streamed_promise: StreamedPromise) -> AsyncIterator[int]:
        nonlocal producer_iterations
        for i in range(1, 6):
            producer_iterations += 1
            yield i

    async def packager(_streamed_promise: StreamedPromise) -> list[int]:
        return [piece async for piece in _streamed_promise]

    async with PromiseContext():
        streamed_promise = StreamedPromise(
            producer=producer,
            packager=packager,
            schedule_immediately=schedule_immediately,
        )

        assert [i async for i in streamed_promise] == [1, 2, 3, 4, 5]
        # iterate over the promise again
        assert [i async for i in streamed_promise] == [1, 2, 3, 4, 5]

    # test that the producer is not called multiple times (only 5 real iterations should happen)
    assert producer_iterations == 5


@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_stream_replay_iterator_exception(schedule_immediately: bool) -> None:
    """
    Assert that when a `StreamedPromise` is iterated over multiple times and an exception is raised in the middle of
    the `producer` iterations, the exact same sequence of exceptions is replayed.
    """

    with AppendProducer(capture_errors=True) as producer:
        for i in range(1, 6):
            if i == 3:
                raise ValueError("Test error")
            producer.append(i)

    async def packager(_streamed_promise: StreamedPromise) -> list[int]:
        return [piece async for piece in _streamed_promise]

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

    async with PromiseContext():
        streamed_promise = StreamedPromise(
            producer=producer,
            packager=packager,
            schedule_immediately=schedule_immediately,
        )

        await iterate_over_promise()
        # iterate over the stream again
        await iterate_over_promise()


async def _async_producer_but_no_generator(_):
    return  # not a generator


@pytest.mark.parametrize(
    "broken_producer",
    [
        "not really a producer",
        lambda _: iter([]),  # non-async producer
        _async_producer_but_no_generator,
    ],
)
@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_stream_broken_producer(broken_producer, schedule_immediately: bool) -> None:
    """
    Assert that when a `StreamedPromise` tries to iterate over a broken `producer` it does not hang indefinitely, just
    raises an error and stops the stream.
    """

    async def packager(_streamed_promise: StreamedPromise) -> list[int]:
        return [piece async for piece in _streamed_promise]

    async def iterate_over_promise():
        promise_iterator = streamed_promise.__aiter__()

        # noinspection PyTypeChecker
        with pytest.raises((TypeError, AttributeError)):
            await promise_iterator.__anext__()
        with pytest.raises(StopAsyncIteration):
            await promise_iterator.__anext__()
        with pytest.raises(StopAsyncIteration):
            await promise_iterator.__anext__()

    async with PromiseContext():
        # noinspection PyTypeChecker
        streamed_promise = StreamedPromise(
            producer=broken_producer,
            packager=packager,
            schedule_immediately=schedule_immediately,
        )

        await iterate_over_promise()
        # iterate over the stream again
        await iterate_over_promise()


@pytest.mark.parametrize(
    "broken_packager",
    [
        "not really a packager",
        lambda _: [],  # non-async packager
        TypeError,
    ],
)
@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_stream_broken_packager(broken_packager, schedule_immediately: bool) -> None:
    """
    Assert that if `packager` is broken, `StreamedPromise` still functions and only fails upon `acollect()`.
    """
    expected_packager_call_count = 0  # we are not counting packager calls for completely broken packagers (too hard)
    actual_packager_call_count = 0
    if isinstance(broken_packager, type):
        expected_packager_call_count = 1  # we are counting packager calls for the partially broken packager
        error_class = broken_packager

        async def broken_packager(_streamed_promise: StreamedPromise) -> None:  # pylint: disable=function-redefined
            nonlocal actual_packager_call_count
            actual_packager_call_count += 1
            raise error_class("Test error")

    with AppendProducer(capture_errors=True) as producer:
        for i in range(1, 6):
            producer.append(i)

    async with PromiseContext():
        # noinspection PyTypeChecker
        streamed_promise = StreamedPromise(
            producer=producer,
            packager=broken_packager,
            schedule_immediately=schedule_immediately,
        )

        with pytest.raises(TypeError) as exc_info1:
            await streamed_promise.acollect()
        error1 = exc_info1.value

        assert [i async for i in streamed_promise] == [1, 2, 3, 4, 5]

        with pytest.raises(TypeError) as exc_info2:
            await streamed_promise.acollect()

    assert error1 is exc_info2.value  # exact same error instance should be raised again

    assert actual_packager_call_count == expected_packager_call_count


@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_streamed_promise_acollect(schedule_immediately: bool) -> None:
    """
    Assert that:
    - when a `StreamedPromise` is "collected" multiple times, the `packager` is only called once;
    - the exact same instance of the result object is returned from `acollect()` when it is called again.
    """
    packager_calls = 0

    with AppendProducer(capture_errors=False) as producer:
        for i in range(1, 6):
            producer.append(i)

    async def packager(_streamed_promise: StreamedPromise) -> list[int]:
        nonlocal packager_calls
        packager_calls += 1
        return [piece async for piece in _streamed_promise]

    async with PromiseContext():
        streamed_promise = StreamedPromise(
            producer=producer,
            packager=packager,
            schedule_immediately=schedule_immediately,
        )

        result1 = await streamed_promise.acollect()
        # "collect from the stream" again
        result2 = await streamed_promise.acollect()

        # test that the packager is not called multiple times
        assert packager_calls == 1

        assert result1 == [1, 2, 3, 4, 5]
        assert result2 is result1  # the promise should always return the exact same instance of the result object


@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_append_producer_dont_capture_errors(schedule_immediately: bool) -> None:
    """
    Assert that when `AppendProducer` is not capturing errors, then:
    - the error is raised beyond the context manager;
    - the `StreamedPromise` is not affected by the error and is just returning the elements up to the error.
    """
    with pytest.raises(ValueError):
        with AppendProducer(capture_errors=False) as producer:
            for i in range(1, 6):
                if i == 3:
                    raise ValueError("Test error")
                producer.append(i)

    async def packager(_streamed_promise: StreamedPromise) -> list[int]:
        return [piece async for piece in _streamed_promise]

    async with PromiseContext():
        streamed_promise = StreamedPromise(
            producer=producer,
            packager=packager,
            schedule_immediately=schedule_immediately,
        )

        assert await streamed_promise.acollect() == [1, 2]


@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_streamed_promise_same_instance(schedule_immediately: bool) -> None:
    """
    Assert that `producer` and `packager` receive the exact same instance of `StreamedPromise`.
    """

    # noinspection PyTypeChecker
    async def producer(_streamed_promise: StreamedPromise) -> AsyncIterator[int]:
        assert _streamed_promise is streamed_promise
        yield 1

    async def packager(_streamed_promise: StreamedPromise) -> list[int]:
        assert _streamed_promise is streamed_promise
        return [piece async for piece in _streamed_promise]

    async with PromiseContext():
        streamed_promise = StreamedPromise(
            producer=producer,
            packager=packager,
            schedule_immediately=schedule_immediately,
        )

        await streamed_promise.acollect()
