# pylint: disable=wrong-import-position
"""
Code example for using Anthropic Claude.
"""

import asyncio

# noinspection PyUnresolvedReferences
import readline  # pylint: disable=unused-import
from pprint import pprint
from typing import Any

from dotenv import load_dotenv

from miniagents.promisegraph.node import Node
from miniagents.promisegraph.typing import PromiseBound

load_dotenv()

from miniagents.ext.llms.anthropic import create_anthropic_agent
from miniagents.miniagents import MiniAgents

anthropic_agent = create_anthropic_agent()

mini_agents = MiniAgents()


@mini_agents.on_promise_collected
async def on_promise_collected(_: PromiseBound, result: Any) -> None:
    """
    TODO Oleksandr: docstring
    """
    if isinstance(result, Node):
        print()
        print()
        print("HASH KEY:", result.hash_key)
        pprint(result.model_dump(), width=119)
        print()
        print()


async def main() -> None:
    """
    Send a message to Claude and print the response.
    """
    async with mini_agents:
        reply_sequence = anthropic_agent.inquire(
            "How are you today?",
            model="claude-3-haiku-20240307",  # "claude-3-opus-20240229",
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


if __name__ == "__main__":
    asyncio.run(main())
