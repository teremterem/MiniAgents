# noinspection PyUnresolvedReferences
"""
Test the LLM agents.
"""

from typing import Callable

import pytest
from dotenv import load_dotenv

from miniagents.messages import Message
from miniagents.miniagents import MiniAgents, MiniAgent

load_dotenv()

# pylint: disable=wrong-import-position
from miniagents.ext.llm.anthropic import anthropic_agent
from miniagents.ext.llm.openai import create_openai_agent


def _check_openai_response(message: Message) -> None:
    assert message.text.strip() == "I AM ONLINE"
    assert message.choices[0].finish_reason == "stop"


def _check_anthropic_response(message: Message) -> None:
    assert message.text.strip() == "I AM ONLINE"
    assert message.stop_reason == "end_turn"


@pytest.mark.parametrize(
    "llm_agent, check_response_func",
    [
        (create_openai_agent(model="gpt-3.5-turbo-0125"), _check_openai_response),
        (anthropic_agent.fork(model="claude-3-haiku-20240307"), _check_anthropic_response),
    ],
)
@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
@pytest.mark.parametrize("start_asap", [False, True])
async def test_llm(
    start_asap: bool,
    stream: bool,
    llm_agent: MiniAgent,
    check_response_func: Callable[[Message], None],
) -> None:
    """
    Assert that all the LLM agents can respond to a simple prompt.
    """
    async with MiniAgents(start_everything_asap_by_default=start_asap):
        reply_sequence = llm_agent.inquire(
            Message(text="ANSWER:", role="assistant"),
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
            async for token in msg_promise:
                result += token
            check_response_func(await msg_promise)
    assert result.strip() == "I AM ONLINE"
