"""
Code example for using LLMs.
"""

import asyncio

# noinspection PyUnresolvedReferences
import readline  # pylint: disable=unused-import

from dotenv import load_dotenv

from miniagents.miniagent_typing import MessageType
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext
from miniagents.promising.sentinels import AWAIT
from miniagents.utils import achain_loop

load_dotenv()

# pylint: disable=wrong-import-position
from miniagents.ext.llm.openai import create_openai_agent

mini_agents = MiniAgents()

CHAT_HISTORY: list[MessageType] = []


@miniagent
async def user_agent(ctx: InteractionContext) -> None:
    """
    User agent that sends a message to the assistant and keeps track of the chat history.
    """
    print("\033[92;1m", end="", flush=True)
    async for msg_promise in ctx.messages:
        print(f"\n{msg_promise.preliminary_metadata.agent_alias}: ", end="", flush=True)
        async for token in msg_promise:
            print(token, end="", flush=True)
        print("\n")

    CHAT_HISTORY.append(ctx.messages)
    print("\033[93;1m", end="", flush=True)
    CHAT_HISTORY.append(input("USER: "))

    ctx.reply(CHAT_HISTORY)


async def amain() -> None:
    """
    The main conversation loop.
    """
    async with mini_agents:
        try:
            print()
            await achain_loop(
                [
                    user_agent,
                    AWAIT,
                    create_openai_agent(model="gpt-4o-2024-05-13"),
                ]
            )
        except KeyboardInterrupt:
            ...
        finally:
            print("\033[0m\n")


if __name__ == "__main__":
    asyncio.run(amain())
