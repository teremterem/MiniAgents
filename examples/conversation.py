"""
A simple conversation example using the MiniAgents framework.
"""

import logging

from dotenv import load_dotenv

from miniagents.ext.agent_aggregators import dialog_loop
from miniagents.ext.history_agents import markdown_history_agent
from miniagents.ext.llm.openai import openai_agent
from miniagents.miniagents import MiniAgents

load_dotenv()


async def amain() -> None:
    """
    The main conversation loop.
    """
    try:
        print()
        await dialog_loop.fork(
            assistant_agent=openai_agent.fork(model="gpt-4o-2024-05-13"),
            history_agent=markdown_history_agent,
        ).inquire()
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    # logging.getLogger("miniagents.ext.llm").setLevel(logging.DEBUG)

    MiniAgents().run(amain())
