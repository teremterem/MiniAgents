"""
A simple conversation example using the MiniAgents framework.
"""

import logging
from pathlib import Path

from dotenv import load_dotenv

from miniagents.ext.console.console_user_agent import create_console_user_agent
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.miniagents import MiniAgents
from miniagents.utils import adialog_loop

load_dotenv()

CHAT_MD_FILE = Path(__file__).parent / "CHAT.md"


async def amain() -> None:
    """
    The main conversation loop.
    """
    try:
        print()
        await adialog_loop(
            user_agent=create_console_user_agent(chat_history_md_file=CHAT_MD_FILE),
            assistant_agent=create_openai_agent(model="gpt-4o-2024-05-13"),
        )
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    # logging.getLogger("miniagents.ext.llm").setLevel(logging.DEBUG)

    MiniAgents().run(amain())
