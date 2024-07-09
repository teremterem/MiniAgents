"""
This example demonstrates how to use an LLM agent to fix the user's sentences.
"""

from dotenv import load_dotenv

from miniagents import MiniAgents
from miniagents.ext import dialog_loop, console_user_agent
from miniagents.ext.llms import SystemMessage, OpenAIAgent

load_dotenv()


async def main() -> None:
    """
    The main conversation loop.
    """
    dialog_loop.fork(
        user_agent=console_user_agent,
        assistant_agent=OpenAIAgent.fork(model="gpt-4o-2024-05-13"),
    ).kick_off(
        SystemMessage(
            "Your job is to improve the styling and grammar of the sentences that the user throws at you. "
            "Leave the sentences unchanged if they seem fine."
        )
    )


if __name__ == "__main__":
    MiniAgents(llm_logger_agent=True).run(main())
