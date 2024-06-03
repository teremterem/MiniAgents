"""
Tests for the `Message`-based models.
"""

import hashlib
import json

import pytest

from miniagents.messages import Message
from miniagents.promising.ext.frozen import Node
from miniagents.promising.promising import PromisingContext


@pytest.mark.asyncio
async def test_message_nesting_vs_hash_key() -> None:
    """
    Test that the hash key of a message is calculated correctly when it contains nested messages (nested messages
    should be replaced with their respective hash keys when the hash is calculated for the ).
    """

    class SpecialNode(Node):
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
            "text_template": None,
            "extra_field": (
                15,
                {
                    "class_": "Node",
                    "role": "user",
                    "nested_nested__hash_keys": (
                        "47e977f85cff13ea8980cf3d76959caec8a4984a",
                        "91868c8c8398b49deb9a04a73c4ea95bdb2eaa65",
                    ),
                    "nested_nested2__hash_keys": ("91868c8c8398b49deb9a04a73c4ea95bdb2eaa65",),
                },
            ),
            "extra_node": {
                "class_": "SpecialNode",
                "nested_nested__hash_key": "25a897f6457abf51fad6a28d86905918bb610038",
            },
            "nested_message__hash_key": "47e977f85cff13ea8980cf3d76959caec8a4984a",
        }
        assert message.serialize() == expected_structure

        expected_hash_key = hashlib.sha256(
            json.dumps(expected_structure, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()[:40]
        assert message.hash_key == expected_hash_key
