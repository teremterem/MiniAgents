"""
A simple conversation example between the user and an LLM agent using the MiniAgents framework.
"""

import logging

from dotenv import load_dotenv

from miniagents import MiniAgents
from miniagents.ext import dialog_loop, markdown_history_agent, console_user_agent
from miniagents.ext.llm.openai import openai_agent

load_dotenv()


async def main() -> None:
    """
    The main conversation loop.
    """
    await dialog_loop.fork(
        user_agent=console_user_agent.fork(
            # write chat history to a markdown file
            history_agent=markdown_history_agent
        ),
        assistant_agent=openai_agent.fork(model="gpt-4o-2024-05-13"),
    ).inquire()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    # logging.getLogger("miniagents.ext.llm").setLevel(logging.DEBUG)

    MiniAgents().run(main())
