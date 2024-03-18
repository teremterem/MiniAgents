"""
This module will later be split into multiple modules.
"""
import hashlib
import json
from functools import cached_property

from pydantic import BaseModel, ConfigDict


class Node(BaseModel):
    """
    TODO Oleksnadr: update this docstring a bit ?
    A base class for immutable pydantic objects. It is frozen and has a git-style hash key that is calculated from the
    JSON representation of the object.
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

    # TODO Oleksandr: copy-paste Immutable methods that freeze mutable field values (lists, dicts, sets)

class Promise:
    pass


class PromisePath:
    pass
