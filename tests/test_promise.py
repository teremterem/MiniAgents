"""
Tests for the `StreamedPromise` class.
"""

from typing import AsyncIterator

import pytest

from miniagents.promising.promising import StreamedPromise, StreamAppender, PromisingContext


@pytest.mark.parametrize("start_asap", [False, True, None])
@pytest.mark.asyncio
async def test_stream_replay_iterator(start_asap: bool) -> None:
    """
    Assert that when a `StreamedPromise` is iterated over multiple times, the `streamer` is only called once.
    """
    streamer_iterations = 0

    async def streamer(_streamed_promise: StreamedPromise) -> AsyncIterator[int]:
        nonlocal streamer_iterations
        for i in range(1, 6):
            streamer_iterations += 1
            yield i

    async def resolver(_streamed_promise: StreamedPromise) -> list[int]:
        return [piece async for piece in _streamed_promise]

    async with PromisingContext():
        streamed_promise = StreamedPromise(
            streamer=streamer,
            resolver=resolver,
            start_asap=start_asap,
        )

        assert [i async for i in streamed_promise] == [1, 2, 3, 4, 5]
        # iterate over the promise again
        assert [i async for i in streamed_promise] == [1, 2, 3, 4, 5]

    # test that the streamer is not called multiple times (only 5 real iterations should happen)
    assert streamer_iterations == 5


@pytest.mark.parametrize("start_asap", [False, True, None])
@pytest.mark.asyncio
async def test_stream_replay_iterator_exception(start_asap: bool) -> None:
    """
    Assert that when a `StreamedPromise` is iterated over multiple times and an exception is raised in the middle of
    the `streamer` iterations, the exact same sequence of exceptions is replayed.
    """
    async with PromisingContext():
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

        streamed_promise = StreamedPromise(
            streamer=appender,
            resolver=resolver,
            start_asap=start_asap,
        )

        await iterate_over_promise()
        # iterate over the stream again
        await iterate_over_promise()


async def _async_streamer_but_not_generator(_):
    return  # not a generator


@pytest.mark.parametrize(
    "broken_streamer",
    [
        lambda _: iter([]),  # non-async streamer
        _async_streamer_but_not_generator,
    ],
)
@pytest.mark.parametrize("start_asap", [False, True, None])
@pytest.mark.asyncio
async def test_broken_streamer(broken_streamer, start_asap: bool) -> None:
    """
    Assert that when a `StreamedPromise` tries to iterate over a broken `streamer` it does not hang indefinitely, just
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
            streamer=broken_streamer,
            resolver=resolver,
            start_asap=start_asap,
        )

        await iterate_over_promise()
        # iterate over the stream again
        await iterate_over_promise()


@pytest.mark.parametrize(
    "broken_resolver",
    [
        lambda _: [],  # non-async resolver
        TypeError,
    ],
)
@pytest.mark.parametrize("start_asap", [False, True, None])
@pytest.mark.asyncio
async def test_broken_stream_resolver(broken_resolver, start_asap: bool) -> None:
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

    async with PromisingContext():
        with StreamAppender(capture_errors=True) as appender:
            for i in range(1, 6):
                appender.append(i)

        streamed_promise = StreamedPromise(
            streamer=appender,
            resolver=broken_resolver,
            start_asap=start_asap,
        )

        with pytest.raises(TypeError) as exc_info1:
            await streamed_promise
        error1 = exc_info1.value

        assert [i async for i in streamed_promise] == [1, 2, 3, 4, 5]

        with pytest.raises(TypeError) as exc_info2:
            await streamed_promise

    assert error1 is exc_info2.value  # exact same error instance should be raised again

    assert actual_resolver_call_count == expected_resolver_call_count


@pytest.mark.parametrize("start_asap", [False, True, None])
@pytest.mark.asyncio
async def test_streamed_promise_aresolve(start_asap: bool) -> None:
    """
    Assert that:
    - when a `StreamedPromise` is "resolved" multiple times, the `resolver` is only called once;
    - the exact same instance of the result object is returned from `aresolve()` when it is called again.
    """
    resolver_calls = 0

    async with PromisingContext():
        with StreamAppender(capture_errors=False) as appender:
            for i in range(1, 6):
                appender.append(i)

        async def resolver(_streamed_promise: StreamedPromise) -> list[int]:
            nonlocal resolver_calls
            resolver_calls += 1
            return [piece async for piece in _streamed_promise]

        streamed_promise = StreamedPromise(
            streamer=appender,
            resolver=resolver,
            start_asap=start_asap,
        )

        result1 = await streamed_promise
        # "collect from the stream" again
        result2 = await streamed_promise

        # test that the resolver is not called multiple times
        assert resolver_calls == 1

        assert result1 == [1, 2, 3, 4, 5]
        assert result2 is result1  # the promise should always return the exact same instance of the result object


@pytest.mark.parametrize("start_asap", [False, True, None])
@pytest.mark.asyncio
async def test_stream_appender_dont_capture_errors(start_asap: bool) -> None:
    """
    Assert that when `StreamAppender` is not capturing errors, then:
    - the error is raised beyond the context manager;
    - the `StreamedPromise` is not affected by the error and is just returning the elements up to the error.
    """
    async with PromisingContext():
        with pytest.raises(ValueError):
            with StreamAppender(capture_errors=False) as appender:
                for i in range(1, 6):
                    if i == 3:
                        raise ValueError("Test error")
                    appender.append(i)

        async def resolver(_streamed_promise: StreamedPromise) -> list[int]:
            return [piece async for piece in _streamed_promise]

        streamed_promise = StreamedPromise(
            streamer=appender,
            resolver=resolver,
            start_asap=start_asap,
        )

        assert await streamed_promise == [1, 2]


@pytest.mark.parametrize("start_asap", [False, True, None])
@pytest.mark.asyncio
async def test_streamed_promise_same_instance(start_asap: bool) -> None:
    """
    Assert that `streamer` and `resolver` receive the exact same instance of `StreamedPromise`.
    """

    async def streamer(_streamed_promise: StreamedPromise) -> AsyncIterator[int]:
        assert _streamed_promise is streamed_promise
        yield 1

    async def resolver(_streamed_promise: StreamedPromise) -> list[int]:
        assert _streamed_promise is streamed_promise
        return [piece async for piece in _streamed_promise]

    async with PromisingContext():
        streamed_promise = StreamedPromise(
            streamer=streamer,
            resolver=resolver,
            start_asap=start_asap,
        )

        await streamed_promise
