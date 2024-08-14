"""
Tests for the `Message`-based models.
"""

import hashlib
import json

import pytest

from miniagents import Message, MiniAgents
from miniagents.promising.ext.frozen import Frozen
from miniagents.promising.promising import Promise, PromisingContext


@pytest.mark.asyncio
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
        message = Message(
            content="юнікод",
            extra_field=[
                15,
                {
                    "role": "user",
                    "nested_nested": (Message(content="nested_text"), Message(content="nested_text2")),
                    "nested_nested2": [Message(content="nested_text2")],
                },
            ],
            extra_node=SpecialNode(nested_nested=Message(content="nested_text3")),
            nested_message=Message(content="nested_text"),
        )

        expected_structure = {
            "class_": "Message",
            "content": "юнікод",
            "content_template": None,
            "extra_field": (
                15,
                {
                    "class_": "Frozen",
                    "role": "user",
                    "nested_nested__hash_keys": (
                        "03ebecb2b3a3d5508ea47adf49fb9dfcefec45c6",
                        "b4b1128ee0d4be12150e3e5f69b5d7f302db689f",
                    ),
                    "nested_nested2__hash_keys": ("b4b1128ee0d4be12150e3e5f69b5d7f302db689f",),
                },
            ),
            "extra_node": {
                "class_": "SpecialNode",
                "nested_nested__hash_key": "af776c46f2e2c2e01e159cd8622320686bc6b4b2",
            },
            "nested_message__hash_key": "03ebecb2b3a3d5508ea47adf49fb9dfcefec45c6",
        }
        assert message.serialize() == expected_structure

        expected_hash_key = hashlib.sha256(
            json.dumps(expected_structure, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()[:40]
        assert message.hash_key == expected_hash_key


# noinspection PyAsyncCall
@pytest.mark.parametrize("start_asap", [False, True, None])
@pytest.mark.asyncio
async def test_on_persist_message_event_called_once(start_asap: bool) -> None:
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
        Promise(prefill_result=some_message, start_asap=start_asap)
        Promise(prefill_result=some_message, start_asap=start_asap)

    assert promise_resolved_calls == 2  # on_promise_resolved should be called twice regardless
    assert persist_message_calls == 1


@pytest.mark.parametrize("start_asap", [False, True, None])
@pytest.mark.asyncio
async def test_on_persist_message_event_called_twice(start_asap: bool) -> None:
    """
    Assert that the `on_persist_message` event is called twice if two different Messages are resolved.
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
    message2 = Message()

    async with MiniAgents(
        on_promise_resolved=on_promise_resolved,
        on_persist_message=on_persist_message,
    ):
        Promise(prefill_result=message1, start_asap=start_asap)
        Promise(prefill_result=message2, start_asap=start_asap)

    assert promise_resolved_calls == 2  # on_promise_resolved should be called twice regardless
    assert persist_message_calls == 2


@pytest.mark.parametrize("start_asap", [False, True, None])
@pytest.mark.asyncio
async def test_on_persist_message_event_not_called(start_asap: bool) -> None:
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
        Promise(prefill_result=not_a_message, start_asap=start_asap)
        Promise(prefill_result=not_a_message, start_asap=start_asap)

    assert promise_resolved_calls == 2  # on_promise_resolved should be called twice regardless
    assert persist_message_calls == 0


def test_message_content_template() -> None:
    """
    Test that the variable substitution in the content template works as expected.
    """
    message = Message(
        "Some content",
        content_template="Hello, {name}! I am {class_}. Here is some content: {content}",
        name="Alice",
    )
    assert str(message) == "Hello, Alice! I am Message. Here is some content: Some content"
