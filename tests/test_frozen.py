# pylint: disable=redefined-outer-name
"""
Tests for the `Frozen`-based models.
"""

import hashlib
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum as PyEnum
from ipaddress import IPv4Address, IPv6Address
from pathlib import Path
from typing import Optional
from unittest.mock import patch
from uuid import UUID

import pytest
from pydantic import ValidationError

from miniagents.promising.ext.frozen import Frozen
from miniagents.promising.promising import PromisingContext


class SampleEnum(PyEnum):
    OPTION_A = "value_a"
    OPTION_B = "value_b"


@pytest.fixture
def frozen_with_all_types() -> Frozen:
    """
    Provides a Frozen object populated with all allowed immutable types.
    """
    return Frozen(
        field_none=None,
        field_str="hello world",
        field_int=123,
        field_float=45.67,
        field_bool_true=True,
        field_bool_false=False,
        field_uuid=UUID("123e4567-e89b-12d3-a456-426614174000"),
        field_datetime=datetime(2023, 10, 26, 12, 30, 15),
        field_date=date(2023, 10, 26),
        field_time=time(12, 30, 15),
        field_timedelta=timedelta(days=1, hours=2, minutes=30),
        field_decimal=Decimal("123.456789"),
        field_path=Path("/usr/local/bin"),
        field_ipv4=IPv4Address("192.168.1.1"),
        field_ipv6=IPv6Address("2001:0db8:85a3:0000:0000:8a2e:0370:7334"),
        field_enum=SampleEnum.OPTION_A,
        field_bytes="some bytes".encode("utf-8"),
        field_frozenset=frozenset([1, "two", True, SampleEnum.OPTION_B, UUID("abcdef01-2345-6789-abcd-ef0123456789")]),
        field_tuple=("text", 99, False, Path("/tmp")),
        field_nested_frozen=Frozen(nested_str="nested value", nested_int=789),
        field_list_to_tuple=[10, "eleven", datetime(2024, 1, 1)],
        field_dict_to_frozen={"key1": "value1", "key2": 200},
    )


class SampleModel(Frozen):
    """
    A sample immutable subclass that is derived from `Frozen`.
    """

    some_req_field: str
    some_opt_field: int = 2
    sub_model: Optional["SampleModel"] = None


def test_sample_model_frozen() -> None:
    """
    Test that the models of `SampleModel`, which is derived from `Frozen`, are frozen.
    """
    sample = SampleModel(some_req_field="test")

    with pytest.raises(ValidationError):
        sample.some_req_field = "test2"
    with pytest.raises(ValidationError):
        sample.some_opt_field = 3

    assert sample.some_req_field == "test"
    assert sample.some_opt_field == 2


def test_model_frozen() -> None:
    """
    Test that the models of the original `Frozen` class are frozen.
    """
    model = Frozen(some_field="some value")

    with pytest.raises(ValidationError):
        model.some_other_field = "some other value"

    assert model.some_field == "some value"


async def test_sample_model_hash_key() -> None:
    """
    Test `SampleModel.hash_key` property.
    """
    async with PromisingContext():
        sample = SampleModel(some_req_field="test", sub_model=SampleModel(some_req_field="юнікод", some_opt_field=3))
        # Let's make sure that private instance attributes that were not declared in the model beforehand:
        #  1) are settable despite the model being frozen;
        #  2) do not influence the hash_key.
        # MiniAgents.on_persist_message event sets a private attribute on Message instances, hence we want to
        # ensure these properties.
        # pylint: disable=protected-access,attribute-defined-outside-init
        sample._some_private_attribute = "some value"

        # print(json.dumps(sample.model_dump(), ensure_ascii=False, sort_keys=True))
        expected_hash_key = hashlib.sha256(
            '{"class_": "SampleModel", "some_opt_field": 2, "some_req_field": "test", "sub_model": '
            '{"class_": "SampleModel", "some_opt_field": 3, "some_req_field": "юнікод", "sub_model": null}}'
            "".encode("utf-8")
        ).hexdigest()[:40]
        assert sample.hash_key == expected_hash_key


async def test_model_hash_key() -> None:
    """
    Test the original `Frozen.hash_key` property.
    """
    async with PromisingContext():
        model = Frozen(content="test", final_sender_alias="user", custom_field={"role": "user"})
        # print(json.dumps(model.model_dump(), ensure_ascii=False, sort_keys=True))
        expected_hash_key = hashlib.sha256(
            '{"class_": "Frozen", "content": "test", "custom_field": {"class_": "Frozen", "role": "user"}, '
            '"final_sender_alias": "user"}'.encode("utf-8")
        ).hexdigest()[:40]
        assert model.hash_key == expected_hash_key


def test_nested_object_not_copied() -> None:
    """
    Test that nested objects are not copied when the outer pydantic model is created.
    """
    sub_model = SampleModel(some_req_field="test")
    sample = SampleModel(some_req_field="test", sub_model=sub_model)

    assert sample.sub_model is sub_model


async def test_hash_key_calculated_once() -> None:
    """
    Test that `SampleModel.hash_key` property is calculated only once and all subsequent calls return the same
    value without calculating it again.
    """
    original_sha256 = hashlib.sha256

    with patch("hashlib.sha256", side_effect=original_sha256) as mock_sha256:
        async with PromisingContext():
            sample = SampleModel(some_req_field="test")
            mock_sha256.assert_not_called()  # not calculated yet

            assert sample.hash_key == "2f9753c92f0452bacafaa606b6076d2bf266e095"
            mock_sha256.assert_called_once()  # calculated once

            assert sample.hash_key == "2f9753c92f0452bacafaa606b6076d2bf266e095"
            mock_sha256.assert_called_once()  # check that it wasn't calculated again


async def test_model_hash_key_vs_key_ordering() -> None:
    """
    Test that `hash_key` of `Frozen` is not affected by the ordering of its fields.
    """
    async with PromisingContext():
        model1 = Frozen(some_field="test", some_other_field=2)
        model2 = Frozen(some_other_field=2, some_field="test")

        assert model1.hash_key == model2.hash_key


def test_frozen_with_all_types_can_be_created(frozen_with_all_types: Frozen) -> None:
    """
    Test that the Frozen object with all types can be created and accessed.
    """
    assert frozen_with_all_types.field_none is None
    assert frozen_with_all_types.field_str == "hello world"
    assert frozen_with_all_types.field_int == 123
    assert frozen_with_all_types.field_float == 45.67
    assert frozen_with_all_types.field_bool_true is True
    assert frozen_with_all_types.field_bool_false is False
    assert frozen_with_all_types.field_uuid == UUID("123e4567-e89b-12d3-a456-426614174000")
    assert frozen_with_all_types.field_datetime == datetime(2023, 10, 26, 12, 30, 15)
    assert frozen_with_all_types.field_date == date(2023, 10, 26)
    assert frozen_with_all_types.field_time == time(12, 30, 15)
    assert frozen_with_all_types.field_timedelta == timedelta(days=1, hours=2, minutes=30)
    assert frozen_with_all_types.field_decimal == Decimal("123.456789")
    assert frozen_with_all_types.field_path == Path("/usr/local/bin")
    assert frozen_with_all_types.field_ipv4 == IPv4Address("192.168.1.1")
    assert frozen_with_all_types.field_ipv6 == IPv6Address("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
    assert frozen_with_all_types.field_enum == SampleEnum.OPTION_A
    assert frozen_with_all_types.field_bytes == "some bytes".encode("utf-8")
    assert frozen_with_all_types.field_frozenset == frozenset(
        [1, "two", True, SampleEnum.OPTION_B, UUID("abcdef01-2345-6789-abcd-ef0123456789")]
    )
    assert frozen_with_all_types.field_tuple == ("text", 99, False, Path("/tmp"))
    assert frozen_with_all_types.field_nested_frozen == Frozen(nested_str="nested value", nested_int=789)
    # For fields that are converted, we check the type and content
    assert isinstance(frozen_with_all_types.field_list_to_tuple, tuple)
    assert frozen_with_all_types.field_list_to_tuple == (10, "eleven", datetime(2024, 1, 1))
    assert isinstance(frozen_with_all_types.field_dict_to_frozen, Frozen)
    assert frozen_with_all_types.field_dict_to_frozen == Frozen(key1="value1", key2=200)
