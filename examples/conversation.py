"""
A simple conversation example using the MiniAgents framework.
"""

import logging

from dotenv import load_dotenv

from miniagents.ext.chat_history_md import ChatHistoryMD
from miniagents.ext.console_user_agent import create_console_user_agent
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.miniagents import MiniAgents
from miniagents.utils import adialog_loop

load_dotenv()


async def amain() -> None:
    """
    The main conversation loop.
    """
    chat_history = ChatHistoryMD("CHAT.md", default_role="assistant")
    try:
        print()
        await adialog_loop(
            user_agent=create_console_user_agent(chat_history=chat_history),
            assistant_agent=create_openai_agent(model="gpt-4o-2024-05-13"),
        )
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    # logging.getLogger("miniagents.ext.llm").setLevel(logging.DEBUG)

    MiniAgents().run(amain())
