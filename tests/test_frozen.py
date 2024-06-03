"""
Tests for the `Frozen`-based models.
"""

import hashlib
from typing import Optional
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from miniagents.promising.ext.frozen import Frozen
from miniagents.promising.promising import PromisingContext


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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_model_hash_key() -> None:
    """
    Test the original `Frozen.hash_key` property.
    """
    async with PromisingContext():
        model = Frozen(content="test", final_sender_alias="user", custom_field={"role": "user"})
        # print(json.dumps(model.model_dump(exclude={"forum_trees"}), ensure_ascii=False, sort_keys=True))
        expected_hash_key = hashlib.sha256(
            '{"class_": "Frozen", "content": "test", "custom_field": {"class_": "Frozen", "role": "user"}, '
            '"final_sender_alias": "user"}'.encode("utf-8")
        ).hexdigest()[:40]
        assert model.hash_key == expected_hash_key


def test_nested_object_not_copied() -> None:
    """
    Test that nested objects are not copied when the outer pydantic model is created.
    TODO Oleksandr: why do you care about this ?
    """
    sub_model = SampleModel(some_req_field="test")
    sample = SampleModel(some_req_field="test", sub_model=sub_model)

    assert sample.sub_model is sub_model


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_model_hash_key_vs_key_ordering() -> None:
    """
    Test that `hash_key` of `Frozen` is not affected by the ordering of its fields.
    """
    async with PromisingContext():
        model1 = Frozen(some_field="test", some_other_field=2)
        model2 = Frozen(some_other_field=2, some_field="test")

        assert model1.hash_key == model2.hash_key
