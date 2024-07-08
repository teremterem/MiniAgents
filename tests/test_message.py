"""
Tests for the `Message`-based models.
"""

import hashlib
import json

import pytest

from miniagents import Message, MiniAgents
from miniagents.promising.ext.frozen import Frozen
from miniagents.promising.promising import PromisingContext, Promise


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
            text="юнікод",
            extra_field=[
                15,
                {
                    "role": "user",
                    "nested_nested": (Message(text="nested_text"), Message(text="nested_text2")),
                    "nested_nested2": [Message(text="nested_text2")],
                },
            ],
            extra_node=SpecialNode(nested_nested=Message(text="nested_text3")),
            nested_message=Message(text="nested_text"),
        )

        expected_structure = {
            "class_": "Message",
            "text": "юнікод",
            "content_template": None,
            "extra_field": (
                15,
                {
                    "class_": "Frozen",
                    "role": "user",
                    "nested_nested__hash_keys": (
                        "3275491949deff73da05e207b9e7d2142149fa72",
                        "e2212ae920e280316155704074f98b3fcd9ef092",
                    ),
                    "nested_nested2__hash_keys": ("e2212ae920e280316155704074f98b3fcd9ef092",),
                },
            ),
            "extra_node": {
                "class_": "SpecialNode",
                "nested_nested__hash_key": "5c8a6949584202a1553f7efdb728e21078719f4d",
            },
            "nested_message__hash_key": "3275491949deff73da05e207b9e7d2142149fa72",
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
