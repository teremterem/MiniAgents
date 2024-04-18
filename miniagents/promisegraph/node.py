"""
The main class in this module is `Node`. See its docstring for more information.
"""

import hashlib
import json
from functools import cached_property
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class Node(BaseModel):
    """
    A frozen pydantic model that allows arbitrary fields, has a git-style hash key that is calculated from the
    JSON representation of its data. The data is recursively validated to be immutable. Dicts are converted to
    `Node` instances, lists and tuples are converted to tuples of immutable values, sets are prohibited.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    class_: str

    def __str__(self) -> str:
        return self.as_string

    @cached_property
    def as_string(self) -> str:
        """
        Return a string representation of this node.
        """
        # NOTE: child classes should override the private version, `_as_string()` if they want to customize behaviour
        return self._as_string()

    @cached_property
    def as_json(self) -> str:
        """
        Get the JSON representation of the object.
        """
        return json.dumps(self.model_dump(), ensure_ascii=False, sort_keys=True)

    @cached_property
    def hash_key(self) -> str:
        """
        Get the hash key for this object. It is a hash of the JSON representation of the object.
        """
        return hashlib.sha256(self.as_json.encode("utf-8")).hexdigest()

    def serialize_node(self, **model_dump_kwargs) -> dict[str, Any]:
        """
        TODO Oleksandr
        """
        return self.model_dump(**model_dump_kwargs)

    def _as_string(self) -> str:
        """
        Return the message as a string. This is the method that child classes should override to customize the string
        representation of the message.
        """
        return self.as_json

    # noinspection PyNestedDecorators
    @model_validator(mode="before")
    @classmethod
    def _validate_immutable_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively make sure that the field values of the object are immutable.
        """
        # TODO Oleksandr: what about saving fully qualified model name, and not just the short name ?
        values = {"class_": cls.__name__, **values}
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
