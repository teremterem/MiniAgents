"""
Tests for the `Message`-based models.
"""

import hashlib

import pytest

from miniagents.messages import Message
from miniagents.promising.node import Node
from miniagents.promising.promising import PromisingContext


@pytest.mark.asyncio
async def test_message_nesting_vs_hash_key() -> None:
    """
    Test that the hash key of a message is calculated correctly when it contains nested messages (nested messages
    should be replaced with their respective hash keys when the hash is calculated for the ).
    """
    async with PromisingContext():
        message = Message(
            text="text",
            extra_field={
                "role": "user",
                "nested_nested": (Message(text="nested_text"), Message(text="nested_text2")),
                "nested_nested2": [Message(text="nested_text2")],
            },
            extra_node=Node(nested_nested=Message(text="nested_text3")),
            nested_message=Message(text="nested_text"),
        )
        # print(json.dumps(node.model_dump(), ensure_ascii=False, sort_keys=True))
        expected_hash_key = hashlib.sha256(
            '{"class_": "Message", "extra_field": {"class_": "Node", "nested_nested": [{"class_": "Message", '
            '"text": "nested_text", "text_template": null}, {"class_": "Message", "text": "nested_text2", '
            '"text_template": null}], "nested_nested2": [{"class_": "Message", "text": "nested_text2", '
            '"text_template": null}], "role": "user"}, "extra_node": {"class_": "Node", "nested_nested": '
            '{"class_": "Message", "text": "nested_text3", "text_template": null}}, "nested_message": '
            '{"class_": "Message", "text": "nested_text", "text_template": null}, "text": "text", '
            '"text_template": null}'.encode("utf-8")
        ).hexdigest()[:40]
        assert message.hash_key == expected_hash_key
