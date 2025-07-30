import asyncio
from functools import wraps
import inspect
from asyncio import Future
from typing import Any, Callable, Optional, Union

from miniagents.promising.sentinels import NO_VALUE


def cached_privately(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """
    Unlike `@functools.cached_property`, this decorator caches the result of the method call in a private attribute
    instead of replacing the original method with the calculated value. This approach prevents the cached value from
    being registered as a field value in the Pydantic model upon evaluation.

    NOTE: This decorator does not automatically turn the method into a property - you need to additionally decorate
    your method with `@property` on top of this decorator. This decision was made because IDEs like PyCharm don't seem
    to realize that the method became a property if it wasn't explicitly decorated with known decorators like
    `@property` or `@functools.cached_property` (they might have hardcoded this behaviour).
    """

    # TODO can it be made thread-safe ? (for the sake of tricks like `asyncio.to_thread()` and similar)

    @wraps(func)
    def wrapper(self: Any) -> Any:
        # TODO [MINOR] Avoid dynamic construction of the field name upon each call ?
        attr_name = f"__{type(self).__name__}__{func.__name__}__cache"
        result = getattr(self, attr_name, NO_VALUE)
        if result is NO_VALUE:
            result = func(self)
            setattr(self, attr_name, result)
        return result

    return wrapper


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
