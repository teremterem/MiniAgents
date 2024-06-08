"""
The main class in this module is `Frozen`. See its docstring for more information.
"""

import hashlib
import itertools
import json
from functools import cached_property
from typing import Any, Iterator, Optional, Union

from pydantic import BaseModel, ConfigDict, model_validator

FrozenType = Optional[Union[str, int, float, bool, tuple["FrozenType", ...], "Frozen"]]


def freeze_dict_values(d: dict[str, Any]) -> dict[str, FrozenType]:
    """
    Freeze the values of the dictionary using the Frozen class where necessary (and also recursively validate
    the "freezability" of those values). Useful for freezing function kwargs that are going to be supplied
    as (extra) fields of some Frozen object (e.g. a Message) which is meant to be constructed at a later time.
    """
    return dict(Frozen(**d).frozen_fields_and_values(exclude_class=True))


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

    @cached_property
    def as_string(self) -> str:
        """
        Return a string representation of this model. This is usually the representation that will be used when
        the model needs to be a part of an LLM prompts.
        """
        # NOTE: child classes should override the private version, `_as_string()` if they want to customize behaviour
        return self._as_string()

    @cached_property
    def full_json(self) -> str:
        """
        Get the full JSON representation of this Frozen object together with all its nested objects. This is a cached
        property, so it is calculated only the first time it is accessed.
        """
        return self.model_dump_json()

    @cached_property
    def serialized(self) -> str:
        """
        The representation of this Frozen object that you would usually get by calling `serialize()`, but as a string
        with a JSON. This is a cached property, so it is calculated only the first time it is accessed.
        """
        return json.dumps(self.serialize(), ensure_ascii=False, sort_keys=True)

    def serialize(self) -> dict[str, Any]:
        """
        Serialize the object into a dictionary. The default implementation does complete serialization of this
        Frozen object and all its nested objects. Child classes may override this method to customize serialization
        (e.g. externalize certain nested objects and only reference them by their hash keys - see Message).
        """
        return self.model_dump()

    @cached_property
    def hash_key(self) -> str:
        """
        Get the hash key for this object. It is a hash of the JSON representation of the object.
        """
        # pylint: disable=cyclic-import,import-outside-toplevel
        from miniagents.promising.promising import PromisingContext

        hash_key = hashlib.sha256(self.serialized.encode("utf-8")).hexdigest()
        if not PromisingContext.get_current().longer_hash_keys:
            hash_key = hash_key[:40]
        return hash_key

    def frozen_fields(self, exclude_class: bool = False) -> Iterator[str]:
        """
        Get the list of field names of the object. This includes the model fields (both, explicitly set and the ones
        with default values) and the extra fields that are not part of the model.
        """
        if exclude_class:
            return itertools.chain(
                (field for field in self.model_fields if field != "class_"), self.__pydantic_extra__
            )
        return itertools.chain(self.model_fields, self.__pydantic_extra__)

    def frozen_fields_and_values(self, exclude_class: bool = False) -> Iterator[tuple[str, Any]]:
        """
        Get the list of field names and values of the object. This includes the model fields (both, explicitly set
        and the ones with default values) and the extra fields that are not part of the model.
        """
        if exclude_class:
            for field in self.model_fields:
                if field != "class_":
                    yield field, getattr(self, field)
        else:
            for field in self.model_fields:
                yield field, getattr(self, field)

        for field, value in self.__pydantic_extra__.items():  # pylint: disable=no-member
            yield field, value

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
        # TODO Oleksandr: what about saving fully qualified model name, and not just the short name ?
        if "class_" in values:
            if values["class_"] != cls.__name__:
                raise ValueError(
                    f"the `class_` field of a Frozen must be equal to its actual class name, got {values['class_']} "
                    f"instead of {cls.__name__}"
                )
        else:
            values = {"class_": cls.__name__, **values}
        return values

    # noinspection PyNestedDecorators
    @model_validator(mode="before")
    @classmethod
    def _validate_and_freeze_values(cls, values: dict[str, Any]) -> dict[str, FrozenType]:
        """
        Recursively make sure that the field values of the object are immutable and of allowed types.
        """
        values = cls._preprocess_values(values)
        return {key: cls._validate_and_freeze_value(key, value) for key, value in values.items()}

    @classmethod
    def _validate_and_freeze_value(cls, key: str, value: Any) -> FrozenType:
        """
        Recursively make sure that the field value is immutable and of allowed type.
        """
        if isinstance(value, (tuple, list)):
            return tuple(cls._validate_and_freeze_value(key, sub_value) for sub_value in value)
        if isinstance(value, dict):
            return Frozen(**value)
        if not isinstance(value, cls._allowed_value_types()):
            raise ValueError(
                f"only {{{', '.join([t.__name__ for t in cls._allowed_value_types()])}}} "
                f"are allowed as field values in {cls.__name__}, got {type(value).__name__} in `{key}`"
            )
        return value

    @classmethod
    def _allowed_value_types(cls) -> tuple[type[Any], ...]:
        return type(None), str, int, float, bool, tuple, list, dict, Frozen
