"""
Tests for the `MessageSequence` class.
"""

from typing import Optional, Union

import pytest

from miniagents import (
    ErrorMessage,
    Message,
    MessageSequence,
    MessageTokenAppender,
    MiniAgents,
    TextMessage,
    TextToken,
    Token,
)
from miniagents.promising.sentinels import NO_VALUE, Sentinel


@pytest.mark.parametrize("errors_as_messages", [False, True, NO_VALUE])
@pytest.mark.parametrize("start_soon", [False, True, NO_VALUE])
async def test_message_sequence(start_soon: Union[bool, Sentinel], errors_as_messages: Union[bool, Sentinel]) -> None:
    """
    Assert that `MessageSequence` "flattens" a hierarchy of messages into a flat sequence.
    """
    async with MiniAgents():
        msg_seq1 = MessageSequence(
            appender_capture_errors=True,
            start_soon=start_soon,
            # assert that `errors_as_messages` parameter has no effect on the outcome when there are no errors
            errors_as_messages=errors_as_messages,
        )
        with msg_seq1.message_appender:
            msg_seq1.message_appender.append("msg1")
            msg_seq1.message_appender.append({"content": "msg2", "some_attr": 2})
            msg_seq1.message_appender.append(TextMessage("msg3", another_attr=3))

            msg_seq2 = MessageSequence(
                appender_capture_errors=True,
                start_soon=start_soon,
                errors_as_messages=errors_as_messages,
            )
            with msg_seq2.message_appender:
                msg_seq2.message_appender.append("msg4")

                msg_seq3 = MessageSequence(
                    appender_capture_errors=True,
                    start_soon=start_soon,
                    errors_as_messages=errors_as_messages,
                )
                with msg_seq3.message_appender:
                    msg_seq3.message_appender.append("msg5")
                    msg_seq3.message_appender.append(["msg6", "msg7"])
                    msg_seq3.message_appender.append([[TextMessage("msg8", another_attr=8)]])

                msg_seq2.message_appender.append(msg_seq3.sequence_promise)
                msg_seq2.message_appender.append("msg9")

            msg_seq1.message_appender.append(msg_seq2.sequence_promise)
            msg_seq1.message_appender.append(TextMessage.promise("msg10", yet_another_attr=10))
            # msg_seq1.message_appender.append(ValueError("msg11"))

        message_result = [await msg_promise async for msg_promise in msg_seq1.sequence_promise]
        assert message_result == [
            TextMessage("msg1"),
            Message(content="msg2", some_attr=2),
            TextMessage("msg3", another_attr=3),
            TextMessage("msg4"),
            TextMessage("msg5"),
            TextMessage("msg6"),
            TextMessage("msg7"),
            TextMessage("msg8", another_attr=8),
            TextMessage("msg9"),
            TextMessage("msg10", yet_another_attr=10),
            # ValueError("msg11"),
        ]

        token_result = [token async for msg_promise in msg_seq1.sequence_promise async for token in msg_promise]
        assert token_result == [
            TextToken("msg1", content_template=None),
            Token(content="msg2", some_attr=2),
            TextToken("msg3", content_template=None, another_attr=3),
            TextToken("msg4", content_template=None),
            TextToken("msg5", content_template=None),
            TextToken("msg6", content_template=None),
            TextToken("msg7", content_template=None),
            TextToken("msg8", content_template=None, another_attr=8),
            TextToken("msg9", content_template=None),
            TextToken("msg10", content_template=None, yet_another_attr=10),
            # TextToken("msg11", content_template=None),
        ]


@pytest.mark.parametrize("start_soon", [False, True, NO_VALUE])
async def test_message_sequence_error(start_soon: Union[bool, Sentinel]) -> None:
    """
    Assert that `MessageSequence` "flattens" a hierarchy of messages into a flat sequence, but raises an error at
    the right place.
    """
    async with MiniAgents(appenders_capture_errors_by_default=True):
        msg_seq1 = MessageSequence(start_soon=start_soon)
        with msg_seq1.message_appender:
            msg_seq1.message_appender.append("msg1")

            msg_seq2 = MessageSequence(start_soon=start_soon)
            with msg_seq2.message_appender:
                msg_seq2.message_appender.append("msg2")

                msg_seq3 = MessageSequence(start_soon=start_soon)
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
        TextMessage("msg1"),
        TextMessage("msg2"),
        TextMessage("msg3"),
        # ValueError("msg4"),
    ]


@pytest.mark.parametrize("collect_token_by_token", [False, True, None])
@pytest.mark.parametrize("start_soon", [False, True, NO_VALUE])
async def test_message_sequence_error_to_message(
    start_soon: Union[bool, Sentinel], collect_token_by_token: Optional[bool]
) -> None:
    """
    Assert that `MessageSequence` converts errors into messages if `errors_as_messages` is set to `True`.
    """
    async with MiniAgents(appenders_capture_errors_by_default=True):
        msg_seq = MessageSequence(start_soon=start_soon, errors_as_messages=True)
        with msg_seq.message_appender:
            msg_seq.message_appender.append("msg1")
            raise ValueError("error1")

        message_result = await _collect_message_sequence_result(msg_seq, collect_token_by_token)

        if collect_token_by_token:
            assert message_result == [
                TextToken("msg1", content_template=None),
                TextToken("ValueError: error1", content_template=None),
            ]
            assert issubclass([promise async for promise in msg_seq.sequence_promise][-1].message_class, ErrorMessage)
            assert isinstance((await msg_seq.sequence_promise)[-1], ErrorMessage)
        else:
            assert message_result == [
                TextMessage("msg1"),
                ErrorMessage("ValueError: error1"),
            ]


@pytest.mark.parametrize("collect_token_by_token", [False, True, None])
@pytest.mark.parametrize("start_soon", [False, True, NO_VALUE])
async def test_message_sequence_token_error_to_message(
    start_soon: Union[bool, Sentinel], collect_token_by_token: Optional[bool]
) -> None:
    """
    Assert that `MessageSequence` puts token level errors into the message if `errors_as_messages` is set to `True`.
    """
    async with MiniAgents(appenders_capture_errors_by_default=True):
        msg_seq = MessageSequence(start_soon=start_soon, errors_as_messages=True)
        with msg_seq.message_appender:
            msg_seq.message_appender.append("msg1")
            with MessageTokenAppender() as token_appender:
                msg_seq.message_appender.append(Message.promise(message_token_streamer=token_appender))
                token_appender.append("token1")
                token_appender.append("token2")
                raise ValueError("error1")

        result = await _collect_message_sequence_result(msg_seq, collect_token_by_token)

        if collect_token_by_token:
            assert result == [
                TextToken("msg1", content_template=None),
                TextToken("token1"),
                TextToken("token2"),
                TextToken("\nValueError: error1"),
            ]
            assert issubclass(
                [promise async for promise in msg_seq.sequence_promise][-1].message_class,
                Message,  # it will only become an ErrorMessage after faulty token is encountered
            )
            assert isinstance((await msg_seq.sequence_promise)[-1], ErrorMessage)
        else:
            assert result == [
                TextMessage("msg1"),
                ErrorMessage("token1token2\nValueError: error1"),
            ]


async def _collect_message_sequence_result(
    msg_seq: MessageSequence, collect_token_by_token: Optional[bool]
) -> list[Union[str, Message]]:
    if collect_token_by_token is None:
        # None means lets test resolution of the whole sequence at once
        return list(await msg_seq.sequence_promise)

    result = []
    async for msg_promise in msg_seq.sequence_promise:
        if collect_token_by_token:
            async for token in msg_promise:
                result.append(token)
        else:
            result.append(await msg_promise)

    return result
