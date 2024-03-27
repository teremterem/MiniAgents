"""
Tests for the `Node`-based models.
"""

import hashlib
from typing import Optional
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from miniagents.promisegraph.node import Node


class SampleImmutable(Node):
    """A sample immutable subclass that is derived from `Node`."""

    some_req_field: str
    some_opt_field: int = 2
    sub_immutable: Optional["SampleImmutable"] = None


def test_immutable_frozen() -> None:
    """Test that the models of `SampleImmutable`, which is derived from `Node`, are frozen."""

    sample = SampleImmutable(some_req_field="test")

    with pytest.raises(ValidationError):
        sample.some_req_field = "test2"
    with pytest.raises(ValidationError):
        sample.some_opt_field = 3

    assert sample.some_req_field == "test"
    assert sample.some_opt_field == 2


def test_node_frozen() -> None:
    """Test that the models of the original `Node` class are frozen."""
    node = Node(some_field="some value")

    with pytest.raises(ValidationError):
        node.some_other_field = "some other value"

    assert node.some_field == "some value"


def test_sample_immutable_hash_key() -> None:
    """Test `SampleImmutable.hash_key` property."""
    sample = SampleImmutable(
        some_req_field="test", sub_immutable=SampleImmutable(some_req_field="юнікод", some_opt_field=3)
    )

    # print(json.dumps(sample.model_dump(), ensure_ascii=False, sort_keys=True))
    expected_hash_key = hashlib.sha256(
        '{"some_opt_field": 2, "some_req_field": "test", "sub_immutable": '
        '{"some_opt_field": 3, "some_req_field": "юнікод", "sub_immutable": null}}'.encode("utf-8")
    ).hexdigest()
    assert sample.hash_key == expected_hash_key


def test_node_hash_key() -> None:
    """Test the original `Node.hash_key` property."""
    node = Node(content="test", final_sender_alias="user", custom_field={"role": "user"})
    # print(json.dumps(node.model_dump(exclude={"forum_trees"}), ensure_ascii=False, sort_keys=True))
    expected_hash_key = hashlib.sha256(
        '{"content": "test", "custom_field": {"role": "user"}, "final_sender_alias": "user"}'.encode("utf-8")
    ).hexdigest()
    assert node.hash_key == expected_hash_key


def test_nested_object_not_copied() -> None:
    """
    Test that nested objects are not copied when the outer pydantic model is created.
    TODO Oleksandr: why do you care about this ?
    """
    sub_immutable = SampleImmutable(some_req_field="test")
    sample = SampleImmutable(some_req_field="test", sub_immutable=sub_immutable)

    assert sample.sub_immutable is sub_immutable


def test_hash_key_calculated_once() -> None:
    """
    Test that `SampleImmutable.hash_key` property is calculated only once and all subsequent calls return the same
    value without calculating it again.
    """
    original_sha256 = hashlib.sha256

    with patch("hashlib.sha256", side_effect=original_sha256) as mock_sha256:
        sample = SampleImmutable(some_req_field="test")
        mock_sha256.assert_not_called()  # not calculated yet

        assert sample.hash_key == "ca85d50af7d8b17f35ecee07c489705fb1d137bf9e54b53558857abf2b3e672d"
        mock_sha256.assert_called_once()  # calculated once

        assert sample.hash_key == "ca85d50af7d8b17f35ecee07c489705fb1d137bf9e54b53558857abf2b3e672d"
        mock_sha256.assert_called_once()  # check that it wasn't calculated again


def test_node_hash_key_vs_key_ordering() -> None:
    """
    Test that `hash_key` of `Node` is not affected by the ordering of its fields.
    """
    node1 = Node(some_field="test", some_other_field=2)
    node2 = Node(some_other_field=2, some_field="test")

    assert node1.hash_key == node2.hash_key
