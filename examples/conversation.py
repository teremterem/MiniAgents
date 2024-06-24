"""
A simple conversation example using the MiniAgents framework.
"""

import logging

from dotenv import load_dotenv

from miniagents.ext.agent_aggregators import dialog_loop
from miniagents.ext.chat_history_md import chat_history_md_agent
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
            history_agent=chat_history_md_agent.fork(history_md_file="CHAT.md"),
        ).inquire()
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    # logging.getLogger("miniagents.ext.llm").setLevel(logging.DEBUG)

    MiniAgents().run(amain())
