"""
Tests for the `StreamedPromise` class.
"""

from typing import AsyncIterator

import pytest

from miniagents.promising.node import Node
from miniagents.promising.promising import StreamedPromise, StreamAppender, PromisingContext, Promise
from miniagents.promising.sentinels import DEFAULT


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

    async def resolver(_streamed_promise: StreamedPromise) -> list[int]:
        return [piece async for piece in _streamed_promise]

    async with PromisingContext():
        streamed_promise = StreamedPromise(
            producer=producer,
            resolver=resolver,
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

    with StreamAppender(capture_errors=True) as appender:
        for i in range(1, 6):
            if i == 3:
                raise ValueError("Test error")
            appender.append(i)

    async def resolver(_streamed_promise: StreamedPromise) -> list[int]:
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

    async with PromisingContext():
        streamed_promise = StreamedPromise(
            producer=appender,
            resolver=resolver,
            schedule_immediately=schedule_immediately,
        )

        await iterate_over_promise()
        # iterate over the stream again
        await iterate_over_promise()


async def _async_producer_but_not_generator(_):
    return  # not a generator


@pytest.mark.parametrize(
    "broken_producer",
    [
        "not really a producer",
        lambda _: iter([]),  # non-async producer
        _async_producer_but_not_generator,
    ],
)
@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_broken_streamer(broken_producer, schedule_immediately: bool) -> None:
    """
    Assert that when a `StreamedPromise` tries to iterate over a broken `producer` it does not hang indefinitely, just
    raises an error and stops the stream.
    """

    async def resolver(_streamed_promise: StreamedPromise) -> list[int]:
        return [piece async for piece in _streamed_promise]

    async def iterate_over_promise():
        promise_iterator = streamed_promise.__aiter__()

        with pytest.raises((TypeError, AttributeError)):
            await promise_iterator.__anext__()
        with pytest.raises(StopAsyncIteration):
            await promise_iterator.__anext__()
        with pytest.raises(StopAsyncIteration):
            await promise_iterator.__anext__()

    async with PromisingContext():
        streamed_promise = StreamedPromise(
            producer=broken_producer,
            resolver=resolver,
            schedule_immediately=schedule_immediately,
        )

        await iterate_over_promise()
        # iterate over the stream again
        await iterate_over_promise()


@pytest.mark.parametrize(
    "broken_resolver",
    [
        # "not really a resolver",  # TODO Oleksandr: do we even need this particular test case ?
        lambda _: [],  # non-async resolver
        TypeError,
    ],
)
@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_broken_stream_resolver(broken_resolver, schedule_immediately: bool) -> None:
    """
    Assert that if `resolver` is broken, `StreamedPromise` still yields the stream and only fails upon `aresolve()`
    (or bare `await`, for that matter).
    """
    expected_resolver_call_count = 0  # we are not counting resolver calls for completely broken resolvers (too hard)
    actual_resolver_call_count = 0
    if isinstance(broken_resolver, type):
        expected_resolver_call_count = 1  # we are counting resolver calls for the partially broken resolver
        error_class = broken_resolver

        async def broken_resolver(_streamed_promise: StreamedPromise) -> None:  # pylint: disable=function-redefined
            nonlocal actual_resolver_call_count
            actual_resolver_call_count += 1
            raise error_class("Test error")

    with StreamAppender(capture_errors=True) as appender:
        for i in range(1, 6):
            appender.append(i)

    async with PromisingContext():
        streamed_promise = StreamedPromise(
            producer=appender,
            resolver=broken_resolver,
            schedule_immediately=schedule_immediately,
        )

        with pytest.raises(TypeError) as exc_info1:
            await streamed_promise
        error1 = exc_info1.value

        assert [i async for i in streamed_promise] == [1, 2, 3, 4, 5]

        with pytest.raises(TypeError) as exc_info2:
            await streamed_promise

    assert error1 is exc_info2.value  # exact same error instance should be raised again

    assert actual_resolver_call_count == expected_resolver_call_count


@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_streamed_promise_aresolve(schedule_immediately: bool) -> None:
    """
    Assert that:
    - when a `StreamedPromise` is "resolved" multiple times, the `resolver` is only called once;
    - the exact same instance of the result object is returned from `aresolve()` when it is called again.
    """
    resolver_calls = 0

    with StreamAppender(capture_errors=False) as appender:
        for i in range(1, 6):
            appender.append(i)

    async def resolver(_streamed_promise: StreamedPromise) -> list[int]:
        nonlocal resolver_calls
        resolver_calls += 1
        return [piece async for piece in _streamed_promise]

    async with PromisingContext():
        streamed_promise = StreamedPromise(
            producer=appender,
            resolver=resolver,
            schedule_immediately=schedule_immediately,
        )

        result1 = await streamed_promise
        # "collect from the stream" again
        result2 = await streamed_promise

        # test that the resolver is not called multiple times
        assert resolver_calls == 1

        assert result1 == [1, 2, 3, 4, 5]
        assert result2 is result1  # the promise should always return the exact same instance of the result object


@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_stream_appender_dont_capture_errors(schedule_immediately: bool) -> None:
    """
    Assert that when `StreamAppender` is not capturing errors, then:
    - the error is raised beyond the context manager;
    - the `StreamedPromise` is not affected by the error and is just returning the elements up to the error.
    """
    with pytest.raises(ValueError):
        with StreamAppender(capture_errors=False) as appender:
            for i in range(1, 6):
                if i == 3:
                    raise ValueError("Test error")
                appender.append(i)

    async def resolver(_streamed_promise: StreamedPromise) -> list[int]:
        return [piece async for piece in _streamed_promise]

    async with PromisingContext():
        streamed_promise = StreamedPromise(
            producer=appender,
            resolver=resolver,
            schedule_immediately=schedule_immediately,
        )

        assert await streamed_promise == [1, 2]


@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_streamed_promise_same_instance(schedule_immediately: bool) -> None:
    """
    Assert that `producer` and `resolver` receive the exact same instance of `StreamedPromise`.
    """

    async def producer(_streamed_promise: StreamedPromise) -> AsyncIterator[int]:
        assert _streamed_promise is streamed_promise
        yield 1

    async def resolver(_streamed_promise: StreamedPromise) -> list[int]:
        assert _streamed_promise is streamed_promise
        return [piece async for piece in _streamed_promise]

    async with PromisingContext():
        streamed_promise = StreamedPromise(
            producer=producer,
            resolver=resolver,
            schedule_immediately=schedule_immediately,
        )

        await streamed_promise


# noinspection PyAsyncCall
@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_on_node_resolved_event_called_once(schedule_immediately: bool) -> None:
    """
    Assert that the `on_node_resolved` event is called only once if the same Node is resolved multiple times.
    """
    promise_resolved_calls = 0
    node_resolved_calls = 0

    async def on_promise_resolved(_, __) -> None:
        nonlocal promise_resolved_calls
        promise_resolved_calls += 1

    async def on_node_resolved(_, __) -> None:
        nonlocal node_resolved_calls
        node_resolved_calls += 1

    some_node = Node()

    async with PromisingContext(
        on_promise_resolved=on_promise_resolved,
        on_node_resolved=on_node_resolved,
    ):
        Promise(prefill_result=some_node, schedule_immediately=schedule_immediately)
        Promise(prefill_result=some_node, schedule_immediately=schedule_immediately)

    assert promise_resolved_calls == 2  # on_promise_resolved should be called twice regardless
    assert node_resolved_calls == 1


@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_on_node_resolved_event_called_twice(schedule_immediately: bool) -> None:
    """
    Assert that the `on_node_resolved` event is called twice if two different Nodes are resolved.
    """
    promise_resolved_calls = 0
    node_resolved_calls = 0

    async def on_promise_resolved(_, __) -> None:
        nonlocal promise_resolved_calls
        promise_resolved_calls += 1

    async def on_node_resolved(_, __) -> None:
        nonlocal node_resolved_calls
        node_resolved_calls += 1

    node1 = Node()
    node2 = Node()

    async with PromisingContext(
        on_promise_resolved=on_promise_resolved,
        on_node_resolved=on_node_resolved,
    ):
        Promise(prefill_result=node1, schedule_immediately=schedule_immediately)
        Promise(prefill_result=node2, schedule_immediately=schedule_immediately)

    assert promise_resolved_calls == 2  # on_promise_resolved should be called twice regardless
    assert node_resolved_calls == 2


@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_on_node_resolved_event_not_called(schedule_immediately: bool) -> None:
    """
    Assert that the `on_node_resolved` event is not called if the resolved value is not a Node.
    """
    promise_resolved_calls = 0
    node_resolved_calls = 0

    async def on_promise_resolved(_, __) -> None:
        nonlocal promise_resolved_calls
        promise_resolved_calls += 1

    async def on_node_resolved(_, __) -> None:
        nonlocal node_resolved_calls
        node_resolved_calls += 1

    value = "not a node"

    async with PromisingContext(
        on_promise_resolved=on_promise_resolved,
        on_node_resolved=on_node_resolved,
    ):
        Promise(prefill_result=value, schedule_immediately=schedule_immediately)
        Promise(prefill_result=value, schedule_immediately=schedule_immediately)

    assert promise_resolved_calls == 2  # on_promise_resolved should be called twice regardless
    assert node_resolved_calls == 0
