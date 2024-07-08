"""
Tests for the `MessageSequence` class.
"""

import pytest

from miniagents import Message
from miniagents.miniagents import MessageSequence
from miniagents.promising.promising import PromisingContext


@pytest.mark.parametrize("start_asap", [False, True, None])
@pytest.mark.asyncio
async def test_message_sequence(start_asap: bool) -> None:
    """
    Assert that `MessageSequence` "flattens" a hierarchy of messages into a flat sequence.
    """
    async with PromisingContext():
        msg_seq1 = MessageSequence(
            appender_capture_errors=True,
            start_asap=start_asap,
        )
        with msg_seq1.message_appender:
            msg_seq1.message_appender.append("msg1")
            msg_seq1.message_appender.append({"content": "msg2", "some_attr": 2})
            msg_seq1.message_appender.append(Message(content="msg3", another_attr=3))

            msg_seq2 = MessageSequence(
                appender_capture_errors=True,
                start_asap=start_asap,
            )
            with msg_seq2.message_appender:
                msg_seq2.message_appender.append("msg4")

                msg_seq3 = MessageSequence(
                    appender_capture_errors=True,
                    start_asap=start_asap,
                )
                with msg_seq3.message_appender:
                    msg_seq3.message_appender.append("msg5")
                    msg_seq3.message_appender.append(["msg6", "msg7"])
                    msg_seq3.message_appender.append([[Message(content="msg8", another_attr=8)]])

                msg_seq2.message_appender.append(msg_seq3.sequence_promise)
                msg_seq2.message_appender.append("msg9")

            msg_seq1.message_appender.append(msg_seq2.sequence_promise)
            msg_seq1.message_appender.append(Message.promise(content="msg10", yet_another_attr=10))
            # msg_seq1.message_appender.append(ValueError("msg11"))

        message_result = [await msg_promise async for msg_promise in msg_seq1.sequence_promise]
        assert message_result == [
            Message(content="msg1"),
            Message(content="msg2", some_attr=2),
            Message(content="msg3", another_attr=3),
            Message(content="msg4"),
            Message(content="msg5"),
            Message(content="msg6"),
            Message(content="msg7"),
            Message(content="msg8", another_attr=8),
            Message(content="msg9"),
            Message(content="msg10", yet_another_attr=10),
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


@pytest.mark.parametrize("start_asap", [False, True, None])
@pytest.mark.asyncio
async def test_message_sequence_error(start_asap: bool) -> None:
    """
    Assert that `MessageSequence` "flattens" a hierarchy of messages into a flat sequence, but raises an error at
    the right place.
    """
    async with PromisingContext(appenders_capture_errors_by_default=True):
        msg_seq1 = MessageSequence(start_asap=start_asap)
        with msg_seq1.message_appender:
            msg_seq1.message_appender.append("msg1")

            msg_seq2 = MessageSequence(start_asap=start_asap)
            with msg_seq2.message_appender:
                msg_seq2.message_appender.append("msg2")

                msg_seq3 = MessageSequence(start_asap=start_asap)
                with msg_seq3.message_appender:
                    msg_seq3.message_appender.append("msg3")
                    # msg_seq3.message_appender.append(ValueError("msg4"))
                    raise ValueError("msg5")

                msg_seq2.message_appender.append(msg_seq3.sequence_promise)
                msg_seq2.message_appender.append("msg6")

            msg_seq1.message_appender.append(msg_seq2.sequence_promise)
            msg_seq1.message_appender.append("msg7")

        message_result = []
        with pytest.raises(ValueError, match="msg5"):
            async for msg_promise in msg_seq1.sequence_promise:
                message_result.append(await msg_promise)

    assert message_result == [
        Message(content="msg1"),
        Message(content="msg2"),
        Message(content="msg3"),
        # ValueError("msg4"),
    ]
