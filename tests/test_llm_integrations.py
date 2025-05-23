# noinspection PyUnresolvedReferences
"""
Test the LLM agents.
"""

from typing import Callable

import pytest
from dotenv import load_dotenv

from miniagents import Message, MiniAgent, MiniAgents, TextMessage

load_dotenv()

# pylint: disable=wrong-import-position
from miniagents.ext.llms import AnthropicAgent, OpenAIAgent


def _check_openai_response(message: Message) -> None:
    assert isinstance(message, TextMessage)
    assert str(message).strip() == "I AM ONLINE"
    assert message.choices[0].finish_reason == "stop"


def _check_anthropic_response(message: Message) -> None:
    assert isinstance(message, TextMessage)
    assert str(message).strip() == "I AM ONLINE"
    assert message.stop_reason == "end_turn"


@pytest.mark.parametrize(
    "llm_agent, check_response_func",
    [
        (OpenAIAgent.fork(model="gpt-4o-mini"), _check_openai_response),
        (AnthropicAgent.fork(model="claude-3-5-haiku-latest"), _check_anthropic_response),
    ],
)
@pytest.mark.parametrize("stream", [False, True])
@pytest.mark.parametrize("start_soon", [False, True])
@pytest.mark.parametrize("flip_consumption_order", [False, True])
async def test_llm_integration(
    llm_agent: MiniAgent,
    check_response_func: Callable[[Message], None],
    stream: bool,
    start_soon: bool,
    flip_consumption_order: bool,
) -> None:
    """
    Assert that all the LLM agents respond to a simple prompt properly.
    """
    async with MiniAgents(start_everything_soon_by_default=start_soon):
        reply_sequence = llm_agent.trigger(
            TextMessage("ANSWER:", role="assistant"),
            system=(
                "This is a test to verify that you are online. Your response will be validated using a strict "
                "program that does not tolerate any deviations from the expected output at all. Please respond "
                "with these exact words, all capitals and no punctuation: I AM ONLINE"
            ),
            stream=stream,
            max_tokens=20,
            temperature=0,
        )

        result = ""
        async for msg_promise in reply_sequence:
            if flip_consumption_order:
                async for token in msg_promise:
                    result += str(token)
                check_response_func(await msg_promise)
            else:
                check_response_func(await msg_promise)
                async for token in msg_promise:
                    result += str(token)

    assert result.strip() == "I AM ONLINE"
