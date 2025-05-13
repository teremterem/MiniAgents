# pylint: disable=redefined-outer-name
"""
Tests for the `Message`-based models.
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
import hashlib
import json
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError
import pytest

from miniagents import Message, MiniAgents, StrictMessage, TextMessage
from miniagents.promising.ext.frozen import Frozen
from miniagents.promising.promising import Promise, PromisingContext
from miniagents.promising.sentinels import NO_VALUE


async def test_message_nesting_vs_hash_key() -> None:
    """
    Test that the hash key of a message is calculated correctly when it contains nested messages (nested messages
    should be replaced with their respective hash keys when the hash is calculated for the ).
    """

    class SpecialNode(Frozen):
        """
        Needed to check if concrete classes are preserved during copying.
        """

    async with PromisingContext():
        message = TextMessage(
            "юнікод",
            extra_field=[
                15,
                {
                    "role": "user",
                    "nested_nested": (TextMessage("nested_text"), TextMessage("nested_text2")),
                    "nested_nested2": [TextMessage(content="nested_text2")],
                },
            ],
            extra_node=SpecialNode(nested_nested=TextMessage("nested_text3")),
            nested_message=TextMessage("nested_text"),
        )

        expected_structure = {
            "class_": "TextMessage",
            "content": "юнікод",
            "content_template": None,
            "extra_field": [
                15,
                {
                    "class_": "Frozen",
                    "role": "user",
                    "nested_nested__hash_keys": [
                        "05549eba31f5f800e6f720331d99cb93c62cfaab",
                        "73695a09b7a91de152d65fbea44b4813e97ecd9d",
                    ],
                    "nested_nested2__hash_keys": ["73695a09b7a91de152d65fbea44b4813e97ecd9d"],
                },
            ],
            "extra_node": {
                "class_": "SpecialNode",
                "nested_nested__hash_key": "4df48c769ae0669b377dc307f51a8df9cc671cc1",
            },
            "nested_message__hash_key": "05549eba31f5f800e6f720331d99cb93c62cfaab",
        }
        assert message.serialize() == expected_structure

        expected_hash_key = hashlib.sha256(
            json.dumps(expected_structure, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()[:40]
        assert message.hash_key == expected_hash_key


# noinspection PyAsyncCall
@pytest.mark.parametrize("start_soon", [False, True, NO_VALUE])
async def test_on_persist_message_event_called_once(start_soon: bool) -> None:
    """
    Assert that the `on_persist_message` event is called only once if the same Message is resolved multiple times.
    """
    promise_resolved_calls = 0
    persist_message_calls = 0

    async def on_promise_resolved(_, __) -> None:
        nonlocal promise_resolved_calls
        promise_resolved_calls += 1

    async def on_persist_message(_, __) -> None:
        nonlocal persist_message_calls
        persist_message_calls += 1

    some_message = Message()

    async with MiniAgents(
        on_promise_resolved=on_promise_resolved,
        on_persist_message=on_persist_message,
    ):
        Promise(prefill_result=some_message, start_soon=start_soon)
        Promise(prefill_result=some_message, start_soon=start_soon)

    assert promise_resolved_calls == 2  # on_promise_resolved should be called twice regardless
    assert persist_message_calls == 1


@pytest.mark.parametrize("start_soon", [False, True, NO_VALUE])
async def test_on_persist_message_event_called_four_times(start_soon: bool) -> None:
    """
    Assert that the `on_persist_message` event is called four times if four different Messages are resolved.
    """
    promise_resolved_calls = 0
    persist_message_calls = 0

    async def on_promise_resolved(_, __) -> None:
        nonlocal promise_resolved_calls
        promise_resolved_calls += 1

    async def on_persist_message(_, __) -> None:
        nonlocal persist_message_calls
        persist_message_calls += 1

    message1 = Message()
    message2 = TextMessage()
    message3 = Message()
    message4 = TextMessage()

    async with MiniAgents(
        on_promise_resolved=on_promise_resolved,
        on_persist_message=on_persist_message,
    ):
        Promise(prefill_result=message1, start_soon=start_soon)
        Promise(prefill_result=message2, start_soon=start_soon)
        Promise(prefill_result=message3, start_soon=start_soon)
        Promise(prefill_result=message4, start_soon=start_soon)

    assert promise_resolved_calls == 4  # on_promise_resolved should be called four times regardless
    assert persist_message_calls == 4


@pytest.mark.parametrize("start_soon", [False, True, NO_VALUE])
async def test_on_persist_message_event_not_called(start_soon: bool) -> None:
    """
    Assert that the `on_persist_message` event is not called if the resolved value is not a Message.
    """
    promise_resolved_calls = 0
    persist_message_calls = 0

    async def on_promise_resolved(_, __) -> None:
        nonlocal promise_resolved_calls
        promise_resolved_calls += 1

    async def on_persist_message(_, __) -> None:
        nonlocal persist_message_calls
        persist_message_calls += 1

    not_a_message = Frozen(some_field="not a message")

    async with MiniAgents(
        on_promise_resolved=on_promise_resolved,
        on_persist_message=on_persist_message,
    ):
        Promise(prefill_result=not_a_message, start_soon=start_soon)
        Promise(prefill_result=not_a_message, start_soon=start_soon)

    assert promise_resolved_calls == 2  # on_promise_resolved should be called twice regardless
    assert persist_message_calls == 0


def test_message_content_template_and_content() -> None:
    """
    Test that the variable substitution in the content template works as expected (the case when the `content` field
    is provided too).
    """
    message = TextMessage(
        "Some content",
        content_template="Hello, {name}! I am {class_}. Here is some content: {content}",
        name="Alice",
    )
    assert str(message) == "Hello, Alice! I am TextMessage. Here is some content: Some content"


def test_message_content_template_only() -> None:
    """
    Test that the variable substitution in the content template works as expected.
    """
    message = TextMessage(
        content_template="Hello, {name}! I am {class_}. Here is some content: {content}",
        name="Alice",
    )
    assert str(message) == "Hello, Alice! I am TextMessage. Here is some content: None"


def test_strict_message_subclass_extra_field_fails() -> None:
    """
    Test that instantiating a subclass of StrictMessage with an extra field raises a ValidationError.
    """

    class MyStrictMessage(StrictMessage):
        field1: str

    with pytest.raises(ValidationError) as excinfo:
        MyStrictMessage(field1="value1", extra_field="extra_value")

    assert "Extra inputs are not permitted" in str(excinfo.value)


def test_strict_message_subclass_correct_fields_succeeds() -> None:
    """
    Test that instantiating a subclass of StrictMessage with only defined fields succeeds.
    """

    class MyStrictMessage(StrictMessage):
        field1: str
        field2: int = 42

    message = MyStrictMessage(field1="value1")
    assert message.field1 == "value1"
    assert message.field2 == 42

    message = MyStrictMessage(field1="value1", field2=100)
    assert message.field1 == "value1"
    assert message.field2 == 100


def test_strict_message_subclass_is_frozen() -> None:
    """
    Test that subclasses of StrictMessage are frozen (immutable).
    """

    class MyStrictMessage(StrictMessage):
        field1: str

    message = MyStrictMessage(field1="initial_value")

    # Attempt to modify an existing field
    with pytest.raises(ValidationError) as excinfo:
        message.field1 = "new_value"

    assert "Instance is frozen" in str(excinfo.value)
    assert message.field1 == "initial_value"


class SampleEnum(Enum):
    OPTION_A = "value_a"
    OPTION_B = "value_b"


@pytest.fixture
def message_with_all_types() -> Message:
    """
    Provides a Message object populated with all allowed immutable types.
    """
    # pylint: disable=duplicate-code
    message = Message(
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
        field_enum=SampleEnum.OPTION_A,
        field_bytes="some bytes".encode("utf-8"),
        field_frozenset=frozenset(["two"]),
        field_tuple=("text", 99, False, Path("/tmp")),
        field_nested_frozen=Frozen(nested_str="nested value", nested_int=789),
        field_list_to_tuple=[10, "eleven", datetime(2024, 1, 1)],
        field_dict_to_frozen={"key1": "value1", "key2": 200},
    )
    return message


def test_message_with_all_types_can_be_created(message_with_all_types: Message) -> None:
    """
    Test that the Message object with all types can be created and accessed.
    """
    assert message_with_all_types.field_none is None
    assert message_with_all_types.field_str == "hello world"
    assert message_with_all_types.field_int == 123
    assert message_with_all_types.field_float == 45.67
    assert message_with_all_types.field_bool_true is True
    assert message_with_all_types.field_bool_false is False
    assert message_with_all_types.field_uuid == UUID("123e4567-e89b-12d3-a456-426614174000")
    assert message_with_all_types.field_datetime == datetime(2023, 10, 26, 12, 30, 15)
    assert message_with_all_types.field_date == date(2023, 10, 26)
    assert message_with_all_types.field_time == time(12, 30, 15)
    assert message_with_all_types.field_timedelta == timedelta(days=1, hours=2, minutes=30)
    assert message_with_all_types.field_decimal == Decimal("123.456789")
    assert message_with_all_types.field_path == Path("/usr/local/bin")
    assert message_with_all_types.field_enum == SampleEnum.OPTION_A
    assert message_with_all_types.field_bytes == "some bytes".encode("utf-8")
    assert message_with_all_types.field_frozenset == frozenset(["two"])
    assert message_with_all_types.field_tuple == ("text", 99, False, Path("/tmp"))
    assert message_with_all_types.field_nested_frozen == Frozen(nested_str="nested value", nested_int=789)
    # For fields that are converted, we check the type and content
    assert isinstance(message_with_all_types.field_list_to_tuple, tuple)
    assert message_with_all_types.field_list_to_tuple == (10, "eleven", datetime(2024, 1, 1))
    assert isinstance(message_with_all_types.field_dict_to_frozen, Frozen)
    assert message_with_all_types.field_dict_to_frozen == Frozen(key1="value1", key2=200)


# Expected dictionary content after serialization of `frozen_with_all_types` by `model_dump(mode='json')`
EXPECTED_SERIALIZED_DICT_VALUES = {
    "class_": "Message",
    "field_none": None,
    "field_str": "hello world",
    "field_int": 123,
    "field_float": 45.67,
    "field_bool_true": True,
    "field_bool_false": False,
    "field_uuid": "123e4567-e89b-12d3-a456-426614174000",
    "field_datetime": "2023-10-26T12:30:15",
    "field_date": "2023-10-26",
    "field_time": "12:30:15",
    "field_timedelta": "P1DT2H30M",
    "field_decimal": "123.456789",
    "field_path": "/usr/local/bin",
    "field_enum": "value_a",
    "field_bytes": "some bytes",  # Decoded from utf-8 by default in Pydantic's model_dump
    "field_frozenset": ["two"],  # Updated: frozenset becomes a list with one element
    "field_tuple": ["text", 99, False, "/tmp"],  # Tuples become lists, elements serialized
    "field_nested_frozen": {
        "class_": "Frozen",  # Nested Frozen objects also include 'class_'
        "nested_str": "nested value",
        "nested_int": 789,
    },
    "field_list_to_tuple": [10, "eleven", "2024-01-01T00:00:00"],  # List elements serialized
    "field_dict_to_frozen": {
        "class_": "Frozen",  # Dicts converted to Frozen also include 'class_'
        "key1": "value1",
        "key2": 200,
    },
}


def test_message_serialize(message_with_all_types: Message) -> None:
    """
    Test the `serialize()` method of the Message class.
    """
    serialized_dict = message_with_all_types.serialize()

    assert isinstance(serialized_dict, dict)
    assert serialized_dict == EXPECTED_SERIALIZED_DICT_VALUES


def test_message_serialized_property(message_with_all_types: Message) -> None:
    """
    Test the `serialized` property of the Message class.
    """
    serialized_json_str = message_with_all_types.serialized
    assert isinstance(serialized_json_str, str)

    parsed_data = json.loads(serialized_json_str)
    assert parsed_data == EXPECTED_SERIALIZED_DICT_VALUES


def test_message_full_json_property(message_with_all_types: Message) -> None:
    """
    Test the `full_json` property of the Message class.
    """
    full_json_str = message_with_all_types.full_json
    assert isinstance(full_json_str, str)
    assert str(message_with_all_types) == f"```json\n{full_json_str}\n```"

    parsed_data = json.loads(full_json_str)
    assert parsed_data == EXPECTED_SERIALIZED_DICT_VALUES


async def test_message_hash_key_property(message_with_all_types: Message) -> None:
    """
    Test the `hash_key` property of the Message class, ensuring all types are hashable.
    """
    async with PromisingContext():
        assert message_with_all_types.hash_key == "f54fbfdd4d0f4c2e1ff175e992f6776625a38a37"
