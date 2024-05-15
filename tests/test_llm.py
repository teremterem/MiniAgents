"""
Code example for using LLMs.
"""

# noinspection PyUnresolvedReferences
import readline  # pylint: disable=unused-import

import pytest
from dotenv import load_dotenv

load_dotenv()

# pylint: disable=wrong-import-position
# from miniagents.ext.llm.anthropic import create_anthropic_agent
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.miniagents import MiniAgents

# llm_agent = create_anthropic_agent(model="claude-3-haiku-20240307")
llm_agent = create_openai_agent(model="gpt-3.5-turbo-0125")

mini_agents = MiniAgents()


@pytest.mark.asyncio
async def test_llm() -> None:
    async with mini_agents:
        reply_sequence = llm_agent.inquire(
            "How are you today?",
            max_tokens=1000,
            temperature=0.0,
            system="Respond only in Yoda-speak.",
        )

        print()
        async for msg_promise in reply_sequence:
            async for token in msg_promise:
                print(token, end="", flush=True)
            print()
            print()
