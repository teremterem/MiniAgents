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
        Return a string representation of this node. This is usually the representation that will be used when
        the node needs to be a part of an LLM prompts.
        """
        # NOTE: child classes should override the private version, `_as_string()` if they want to customize behaviour
        return self._as_string()

    @cached_property
    def as_json(self) -> str:
        """
        Get the JSON representation of the object. Because it is a property and not a regular method, it always
        returns the complete JSON representation of the object (unlike `serialize_node(**model_dump_kwargs)`, whose
        behaviour can be customized via `**model_dump_kwargs`). This representation is also used to calculate the
        hash key of the node.
        """
        return json.dumps(self.model_dump(), ensure_ascii=False, sort_keys=True)

    @cached_property
    def hash_key(self) -> str:
        """
        Get the hash key for this object. It is a hash of the JSON representation of the object.
        """
        # pylint: disable=cyclic-import,import-outside-toplevel
        from miniagents.promising.promise import PromiseContext

        hash_key = hashlib.sha256(self.as_json.encode("utf-8")).hexdigest()
        if not PromiseContext.get_current().longer_node_hash_keys:
            hash_key = hash_key[:40]
        return hash_key

    def serialize_node(self, **model_dump_kwargs) -> dict[str, Any]:
        """
        Returns a dictionary representation of the node. This method is useful for serialization of the node in order
        to store it in a database or to send it over the network.
        """
        return self.model_dump(**model_dump_kwargs)

    def _as_string(self) -> str:
        """
        Return the message as a string. This is the method that child classes should override to customize the string
        representation of the message for the LLM prompts.
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
        if "class_" in values:
            if values["class_"] != cls.__name__:
                raise ValueError(
                    f"the `class_` field of a Node must be equal to its actual class name, got {values['class_']} "
                    f"instead of {cls.__name__}"
                )
        else:
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
