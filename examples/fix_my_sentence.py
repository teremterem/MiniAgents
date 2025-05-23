"""
This example demonstrates how to use an LLM agent to fix the user's sentences.
"""

from dotenv import load_dotenv
from miniagents import MiniAgents
from miniagents.ext import console_user_agent, dialog_loop
from miniagents.ext.llms import OpenAIAgent, SystemMessage

load_dotenv()


async def main() -> None:
    """
    The main conversation loop.
    """
    dialog_loop.trigger(
        SystemMessage(
            "Your job is to improve the styling and grammar of the sentences that the user throws at you. "
            "Leave the sentences unchanged if they seem fine."
        ),
        user_agent=console_user_agent,
        assistant_agent=OpenAIAgent.fork(model="o4-mini"),
    )


if __name__ == "__main__":
    MiniAgents(llm_logger_agent=True).run(main())
