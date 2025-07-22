import asyncio
import inspect
from asyncio import Future
from typing import Any, Optional, Union


async def acancel_async_object(
    async_object: Any, msg: Optional[Union[str, asyncio.CancelledError]] = None, raise_if_not_cancellable: bool = True
) -> Optional[asyncio.CancelledError]:
    """
    Handle cancellation of async futures, generators, StreamAppenders, etc.

    Args:
        async_object: The async object to cancel (could be a future, a generator, a StreamAppender, etc.)
        msg: The message to put into the `CancelledError` instance, or a `CancelledError` instance itself to use as is
        raise_if_not_cancellable: Whether to raise an error if the async object does not support cancellation

    Returns:
        The `CancelledError` instance that was used to cancel the async object, or `None` if the async object does not
        support cancellation.
    """
    # pylint: disable=import-outside-toplevel,cyclic-import
    from miniagents.promising.promising import StreamAppender

    cancelled_error = prepare_cancelled_error(msg)
    cancelled = False

    if inspect.isasyncgen(async_object):
        try:
            await async_object.athrow(cancelled_error)
        except type(cancelled_error):
            pass
        cancelled = True

    if isinstance(async_object, Future):
        async_object.cancel(str(cancelled_error))
        cancelled = True

    if isinstance(async_object, StreamAppender):
        async_object.cancel(cancelled_error)
        cancelled = True

    if not cancelled and raise_if_not_cancellable:
        raise RuntimeError(f"Object {async_object} does not support cancellation")

    return cancelled_error if cancelled else None


def prepare_cancelled_error(
    msg: Optional[Union[str, asyncio.CancelledError]] = None,
) -> asyncio.CancelledError:
    """
    Prepare a cancelled error to be raised. If `msg` is already a `CancelledError`, return it as is.
    """
    if msg is None:
        return asyncio.CancelledError()
    if isinstance(msg, asyncio.CancelledError):
        return msg
    return asyncio.CancelledError(msg)
