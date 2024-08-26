"""
Tests for the `MessageSequence` class.
"""

import pytest

from miniagents.messages import Message, MessageSequence, MessageTokenAppender
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
                    raise ValueError("error1")

                msg_seq2.message_appender.append(msg_seq3.sequence_promise)
                msg_seq2.message_appender.append("msg6")

            msg_seq1.message_appender.append(msg_seq2.sequence_promise)
            msg_seq1.message_appender.append("msg7")

        message_result = []
        with pytest.raises(ValueError, match="error1"):
            async for msg_promise in msg_seq1.sequence_promise:
                message_result.append(await msg_promise)

    assert message_result == [
        Message(content="msg1"),
        Message(content="msg2"),
        Message(content="msg3"),
        # ValueError("msg4"),
    ]


@pytest.mark.parametrize("start_asap", [False, True, None])
@pytest.mark.asyncio
async def test_message_sequence_error_to_message(start_asap: bool) -> None:
    """
    Assert that `MessageSequence` converts errors into messages if `errors_to_messages` is set to `True`.
    """
    async with PromisingContext(appenders_capture_errors_by_default=True):
        msg_seq = MessageSequence(start_asap=start_asap, errors_to_messages=True)
        with msg_seq.message_appender:
            msg_seq.message_appender.append("msg1")
            raise ValueError("error1")

        message_result = []
        async for msg_promise in msg_seq.sequence_promise:
            message_result.append(await msg_promise)

    assert message_result == [
        Message(content="msg1"),
        Message(content="error1", is_error=True),
    ]


@pytest.mark.parametrize("start_asap", [False, True, None])
@pytest.mark.parametrize("assert_separate_tokens", [False, True, None])
@pytest.mark.asyncio
async def test_message_sequence_token_error_to_message(start_asap: bool, assert_separate_tokens: bool) -> None:
    """
    Assert that `MessageSequence` puts token level errors into the message if `errors_to_messages` is set to `True`.
    """
    async with PromisingContext(appenders_capture_errors_by_default=True):
        msg_seq = MessageSequence(start_asap=start_asap, errors_to_messages=True)
        with msg_seq.message_appender:
            msg_seq.message_appender.append("msg1")
            with MessageTokenAppender() as token_appender:
                msg_seq.message_appender.append(Message.promise(message_token_streamer=token_appender))
                token_appender.append("token1")
                token_appender.append("token2")
                raise ValueError("error1")

        if assert_separate_tokens is None:
            result = list(await msg_seq.sequence_promise)
        else:
            result = []
            async for msg_promise in msg_seq.sequence_promise:
                if assert_separate_tokens:
                    async for token in msg_promise:
                        result.append(token)
                else:
                    result.append(await msg_promise)

    if assert_separate_tokens:
        assert result == [
            "msg1",
            "token1",
            "token2",
            "\nerror1",
        ]
    else:
        assert result == [
            Message(content="msg1"),
            Message(content="token1token2\nerror1"),
        ]
