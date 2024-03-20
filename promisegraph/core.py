"""
TODO Oleksandr: split this module into multiple modules
"""

import hashlib
import json
from functools import cached_property
from typing import Any, TypeVar, Generic, AsyncIterator, Callable, Awaitable, AsyncIterable

from pydantic import BaseModel, ConfigDict, model_validator


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


PART = TypeVar("PART")
WHOLE = TypeVar("WHOLE")


class Promise(Generic[PART, WHOLE]):
    """
    TODO Oleksandr: docstring
    """

    def __init__(
        self,
        producer: Callable[[], AsyncIterator[PART]],
        packager: Callable[[AsyncIterable[PART]], Awaitable[WHOLE]],
    ):
        """
        TODO Oleksandr: replace the definition of `producer` with a protocol ? what about `packager` ?
        TODO Oleksandr: docstring
        """
        self._producer = producer
        self._packager = packager

    def __aiter__(self) -> AsyncIterator[PART]:
        """
        TODO Oleksandr: docstring
        TODO Oleksandr: schedule the `producer` in the __init__ to start at the earliest possible time
        TODO Oleksandr: introduce a proxy that captures all the items produced by the `producer` and collects them
         so the next call to `__aiter__` returns the items from the proxy
        """
        return self._producer()

    async def aresolve(self) -> WHOLE:
        """
        TODO Oleksandr: docstring
        """
        return await self._packager(self)
