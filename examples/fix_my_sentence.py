"""
This example demonstrates how to use an LLM agent to fix the user's sentences.
"""

import logging

from dotenv import load_dotenv

from miniagents.ext.agent_aggregators import dialog_loop
from miniagents.ext.llm.anthropic import anthropic_agent
from miniagents.ext.llm.llm_common import SystemMessage
from miniagents.miniagents import MiniAgents

load_dotenv()


async def amain() -> None:
    """
    The main conversation loop.
    """
    await dialog_loop.fork(assistant_agent=anthropic_agent.fork(model="claude-3-5-sonnet-20240620")).inquire(
        SystemMessage("Your job is to improve the styling and grammar of the sentences that the user throws at you.")
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    # logging.getLogger("miniagents.ext.llm").setLevel(logging.DEBUG)

    MiniAgents().run(amain())
