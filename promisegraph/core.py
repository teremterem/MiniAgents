"""
TODO Oleksandr: split this module into multiple modules
"""

import asyncio
import hashlib
import json
from functools import cached_property
from typing import Any, TypeVar, Generic, AsyncIterator, Callable, Awaitable, AsyncIterable, Union

from pydantic import BaseModel, ConfigDict, model_validator


class Sentinel:
    """A sentinel object that is used indicate things like "no value", "end of queue" etc."""


NO_VALUE = Sentinel()


class Node(BaseModel):
    """
    A frozen pydantic model that allows arbitrary fields, has a git-style hash key that is calculated from the
    JSON representation of its data. The data is recursively validated to be immutable. Dicts are converted to
    `Node` instances, lists and tuples are converted to tuples of immutable values, sets are prohibited.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    @cached_property
    def hash_key(self) -> str:
        """
        Get the hash key for this object. It is a hash of the JSON representation of the object.
        """
        return hashlib.sha256(
            json.dumps(self.model_dump(), ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

    # noinspection PyNestedDecorators
    @model_validator(mode="before")
    @classmethod
    def _validate_immutable_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively make sure that the field values of the object are immutable.
        """
        for key, value in values.items():
            values[key] = cls._validate_value(key, value)
        return values

    @classmethod
    def _validate_value(cls, key: str, value: Any) -> Any:
        """
        Recursively make sure that the field value is immutable.
        """
        if isinstance(value, (tuple, list)):
            return tuple(cls._validate_value(key, sub_value) for sub_value in value)
        if isinstance(value, dict):
            return Node(**value)
        if not isinstance(value, cls._allowed_value_types()):
            raise ValueError(
                f"only {{{', '.join([t.__name__ for t in cls._allowed_value_types()])}}} "
                f"are allowed as field values in {cls.__name__}, got {type(value).__name__} in `{key}`"
            )
        return value

    @classmethod
    def _allowed_value_types(cls) -> tuple[type[Any], ...]:
        return type(None), str, int, float, bool, tuple, list, dict, Node


PIECE = TypeVar("PIECE")
WHOLE = TypeVar("WHOLE")


class StreamedPromise(Generic[PIECE, WHOLE]):
    """
    TODO Oleksandr: docstring
    """

    def __init__(
        self,
        producer: Callable[[], AsyncIterator[PIECE]],
        packager: Callable[[AsyncIterable[PIECE]], Awaitable[WHOLE]],
    ):
        self._producer_iterator = producer()
        self._packager = packager

        self._parts_so_far: list[Union[PIECE, BaseException]] = []
        self._whole = NO_VALUE

        self._producer_finished = False
        self._producer_lock = asyncio.Lock()
        self._packager_lock = asyncio.Lock()

    def __aiter__(self) -> AsyncIterator[PIECE]:
        return _StreamReplayIterator(self)

    async def acollect(self) -> WHOLE:
        """
        TODO Oleksandr: docstring
        """
        if self._whole is NO_VALUE:
            async with self._packager_lock:
                if self._whole is NO_VALUE:
                    self._whole = await self._packager(self)
        return self._whole


# noinspection PyProtectedMember
class _StreamReplayIterator(AsyncIterator[PIECE]):
    def __init__(self, promise: "StreamedPromise") -> None:
        self._promise = promise
        self._index = 0

    async def __anext__(self) -> PIECE:
        if self._index < len(self._promise._parts_so_far):
            item = self._promise._parts_so_far[self._index]
        elif self._promise._producer_finished:
            # StopAsyncIteration is stored as the last item in the parts list
            raise self._promise._parts_so_far[-1]
        else:
            async with self._promise._producer_lock:
                if self._index < len(self._promise._parts_so_far):
                    item = self._promise._parts_so_far[self._index]
                else:
                    item = await self._real_anext()

        self._index += 1

        if isinstance(item, BaseException):
            raise item
        return item

    async def _real_anext(self) -> Union[PIECE, BaseException]:
        # pylint: disable=protected-access
        try:
            item = await self._promise._producer_iterator.__anext__()
        except StopAsyncIteration as exc:
            # StopAsyncIteration will be stored as the last item in the parts list
            item = exc
            self._promise._producer_finished = True
        except BaseException as exc:  # pylint: disable=broad-except
            # any other exception will be stored in the parts list before the StopAsyncIteration
            # (this is because if you keep iterating over an iterator/generator past any regular exception
            # that it might raise, it is still supposed to raise StopAsyncIteration at the end)
            item = exc
        self._promise._parts_so_far.append(item)
        return item
