"""
The main class in this module is `Frozen`. See its docstring for more information.
"""

import hashlib
import json
import os
from numbers import Number
from typing import Any, Optional, Union
from uuid import UUID
from datetime import datetime, date, time, timedelta
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, ConfigDict, model_validator

from miniagents.promising.errors import NoActiveContextError
from miniagents.promising.promise_utils import cached_privately
from miniagents.promising.sentinels import NO_VALUE


LONGER_HASH_KEYS_DEFAULT = os.getenv("FROZEN_LONGER_HASH_KEYS", "false").lower() == "true"

FROZEN_CLASS_FIELD = "class_"


class Frozen(BaseModel):
    """
    A frozen pydantic model that allows arbitrary fields, has a git-style hash key that is calculated from the
    JSON representation of its data. The data is recursively validated to be immutable. Dicts are converted to
    `Frozen` instances, lists and tuples are converted to tuples of immutable values, sets are prohibited.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    class_: str

    def __str__(self) -> str:
        return self.as_string

    def get(self, key: str, default: "FrozenType" = None) -> "FrozenType":
        return getattr(self, key, default)

    def __getitem__(self, item: str) -> "FrozenType":
        return getattr(self, item)

    def __contains__(self, key: Union[str, tuple[str, "FrozenType"]]) -> bool:
        # second part of the condition is for backwards compatibility with the Pydantic itself
        # TODO do we need to maintain a set of keys along with the tuple of keys or there is no benefit ?
        if isinstance(key, str):
            return key in self.keys()
        return key in iter(self)

    @cached_privately
    def keys(self) -> tuple[str, ...]:
        return tuple(key for key, _ in self)

    @cached_privately
    def values(self) -> tuple["FrozenType", ...]:
        return tuple(value for _, value in self)

    def __len__(self) -> int:
        return len(self.keys())

    @property
    @cached_privately
    def as_string(self) -> str:
        """
        Return a string representation of this model. This is usually the representation that will be used when
        the model needs to be a part of an LLM prompts.

        NOTE: child classes should override the private version, `_as_string()` if they want to customize behaviour
        """
        return self._as_string()

    @property
    @cached_privately
    def full_json(self) -> str:
        """
        Get the full JSON representation of this `Frozen` object together with all its nested objects. This is a cached
        property, so it is calculated only the first time it is accessed.

        Unlike the `serialized` property, `full_json` always returns the complete representation of the object
        with all nested objects included directly in the JSON. The `serialized` property, on the other hand,
        may externalize certain nested objects and only include references to them (as implemented by subclasses
        like `Message`). This makes `full_json` suitable for debugging and complete object representation,
        while `serialized` is better for efficient serialization schemes.
        """
        return self.model_dump_json()

    @property
    @cached_privately
    def serialized(self) -> str:
        """
        The representation of this `Frozen` object that you would usually get by calling `serialize()`, but as a string
        with a JSON. This is a cached property, so it is calculated only the first time it is accessed.
        """
        return json.dumps(self.serialize(), ensure_ascii=False, sort_keys=True)

    def serialize(self) -> dict[str, Any]:
        """
        Serialize the object into a dictionary. The default implementation does complete serialization of this
        Frozen object and all its nested objects. Child classes may override this method to customize serialization
        (e.g. externalize certain nested objects and only reference them by their hash keys - see Message).
        """
        return self.model_dump(mode="json")

    @property
    @cached_privately
    def hash_key(self) -> str:
        """
        Get the hash key for this object. It is a hash of the JSON representation of the object.
        """
        # pylint: disable=cyclic-import,import-outside-toplevel
        from miniagents.promising.promising import PromisingContext

        hash_key = hashlib.sha256(self.serialized.encode("utf-8")).hexdigest()

        try:
            longer_hash_keys = PromisingContext.get_current().longer_hash_keys
            if longer_hash_keys is NO_VALUE:
                longer_hash_keys = LONGER_HASH_KEYS_DEFAULT
        except NoActiveContextError:
            longer_hash_keys = LONGER_HASH_KEYS_DEFAULT

        if not longer_hash_keys:
            hash_key = hash_key[:40]
        return hash_key

    def as_kwargs(self) -> dict[str, "FrozenType"]:
        """
        Get a dict of field names and values of this Pydantic object which can be used as keyword arguments for
        a function call ("class_" field is excluded, because it wouldn't likely to make sense as a keyword argument).
        """
        return {key: value for key, value in self if key != FROZEN_CLASS_FIELD}

    def _as_string(self) -> str:
        """
        Return the message as a string. This is the method that child classes should override to customize the string
        representation of the message for the LLM prompts.
        """
        return self.full_json

    @classmethod
    def _preprocess_values(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Preprocess the values before validation and freezing.
        """
        # TODO Either explain in a comment why this field is *silently* overridden whenever it was manually set to a
        #  different value, or prohibit setting it manually altogether with an error
        if values.get(FROZEN_CLASS_FIELD) != cls.__name__:
            # TODO what about saving fully qualified model name, and not just the short name ?
            values = {**values, FROZEN_CLASS_FIELD: cls.__name__}
        return values

    # noinspection PyNestedDecorators
    @model_validator(mode="before")
    @classmethod
    def _validate_and_freeze_values(cls, values: dict[str, Any]) -> dict[str, "FrozenType"]:
        """
        Recursively make sure that the field values of the object are immutable and of allowed types.
        """
        values = cls._preprocess_values(values)
        return {key: cls._validate_and_freeze_value(key, value) for key, value in values.items()}

    @classmethod
    def _validate_and_freeze_value(cls, key: str, value: Any) -> "FrozenType":
        """
        Recursively make sure that the field value is immutable and of allowed type.
        """
        if isinstance(value, (tuple, list)):
            return tuple(cls._validate_and_freeze_value(key, sub_value) for sub_value in value)
        if isinstance(value, dict):
            return Frozen(**value)  # this other instance of Frozen will take care of freezing deeper levels
        if not isinstance(value, cls._allowed_value_types()):
            raise ValueError(
                f"only {{{', '.join([t.__name__ for t in cls._allowed_value_types()])}}} "
                f"are allowed as field values in {cls.__name__}, got {type(value).__name__} in `{key}`"
            )
        return value

    @classmethod
    def _allowed_value_types(cls) -> tuple[type[Any], ...]:
        return (
            type(None),
            str,
            Number,
            bool,
            UUID,
            datetime,
            date,
            time,
            timedelta,
            Path,
            Enum,
            bytes,
            frozenset,
            tuple,
            list,
            dict,
            Frozen,
        )


FrozenType = Optional[
    Union[
        str,
        Number,
        bool,
        UUID,
        datetime,
        date,
        time,
        timedelta,
        Path,
        Enum,
        bytes,
        frozenset["FrozenType"],
        tuple["FrozenType", ...],
        Frozen,
    ]
]


class StrictFrozen(Frozen):
    model_config = ConfigDict(extra="forbid")
