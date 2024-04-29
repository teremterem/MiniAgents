"""
Tests for the `MessageSequence` class.
"""

import pytest

from miniagents.messages import Message
from miniagents.miniagents import MessageSequence
from miniagents.promising.promising import PromisingContext
from miniagents.promising.sentinels import DEFAULT


@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_message_sequence(schedule_immediately: bool) -> None:
    """
    Assert that `MessageSequence` "flattens" a hierarchy of messages into a flat sequence.
    """
    async with PromisingContext():
        msg_seq1 = MessageSequence(
            producer_capture_errors=True,
            schedule_immediately=schedule_immediately,
        )
        with msg_seq1.append_producer:
            msg_seq1.append_producer.append("msg1")
            msg_seq1.append_producer.append({"text": "msg2", "some_attr": 2})
            msg_seq1.append_producer.append(Message(text="msg3", another_attr=3))

            msg_seq2 = MessageSequence(
                producer_capture_errors=True,
                schedule_immediately=schedule_immediately,
            )
            with msg_seq2.append_producer:
                msg_seq2.append_producer.append("msg4")

                msg_seq3 = MessageSequence(
                    producer_capture_errors=True,
                    schedule_immediately=schedule_immediately,
                )
                with msg_seq3.append_producer:
                    msg_seq3.append_producer.append("msg5")
                    msg_seq3.append_producer.append(["msg6", "msg7"])
                    msg_seq3.append_producer.append([[Message(text="msg8", another_attr=8)]])

                msg_seq2.append_producer.append(msg_seq3.sequence_promise)
                msg_seq2.append_producer.append("msg9")

            msg_seq1.append_producer.append(msg_seq2.sequence_promise)
            msg_seq1.append_producer.append(Message.promise(text="msg10", yet_another_attr=10))
            # msg_seq1.append_producer.append(ValueError("msg11"))

        message_result = [await msg_promise.acollect() async for msg_promise in msg_seq1.sequence_promise]
        assert message_result == [
            Message(text="msg1"),
            Message(text="msg2", some_attr=2),
            Message(text="msg3", another_attr=3),
            Message(text="msg4"),
            Message(text="msg5"),
            Message(text="msg6"),
            Message(text="msg7"),
            Message(text="msg8", another_attr=8),
            Message(text="msg9"),
            Message(text="msg10", yet_another_attr=10),
            # ValueError("msg11"),
        ]

        token_result = [token async for msg_promise in msg_seq1.sequence_promise async for token in msg_promise]
        assert token_result == [
            "msg1",
            "msg2",
            "msg3",
            "msg4",
            "msg5",
            "msg6",
            "msg7",
            "msg8",
            "msg9",
            "msg10",
            # "msg11",
        ]


@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_message_sequence_error(schedule_immediately: bool) -> None:
    """
    Assert that `MessageSequence` "flattens" a hierarchy of messages into a flat sequence, but raises an error at
    the right place.
    """
    async with PromisingContext():
        msg_seq1 = MessageSequence(
            producer_capture_errors=True,
            schedule_immediately=schedule_immediately,
        )
        with msg_seq1.append_producer:
            msg_seq1.append_producer.append("msg1")

            msg_seq2 = MessageSequence(
                producer_capture_errors=True,
                schedule_immediately=schedule_immediately,
            )
            with msg_seq2.append_producer:
                msg_seq2.append_producer.append("msg2")

                msg_seq3 = MessageSequence(
                    producer_capture_errors=True,
                    schedule_immediately=schedule_immediately,
                )
                with msg_seq3.append_producer:
                    msg_seq3.append_producer.append("msg3")
                    # msg_seq1.append_producer.append(TypeError("msg4"))
                    raise ValueError("msg5")

                msg_seq2.append_producer.append(msg_seq3.sequence_promise)
                msg_seq2.append_producer.append("msg6")

            msg_seq1.append_producer.append(msg_seq2.sequence_promise)
            msg_seq1.append_producer.append("msg7")

        message_result = []
        with pytest.raises(ValueError, match="msg5"):
            async for msg_promise in msg_seq1.sequence_promise:
                message_result.append(await msg_promise.acollect())

    assert message_result == [
        Message(text="msg1"),
        Message(text="msg2"),
        Message(text="msg3"),
        # ValueError("msg4"),
    ]
