"""
Code example for using LLMs.
"""

import asyncio
from pprint import pprint

from dotenv import load_dotenv

from miniagents.ext.llm.openai import create_openai_agent
from miniagents.messages import Message
from miniagents.miniagents import MiniAgents

load_dotenv()

# logging.basicConfig(level=logging.DEBUG)

# llm_agent = create_anthropic_agent(model="claude-3-haiku-20240307")  # claude-3-opus-20240229
llm_agent = create_openai_agent(model="gpt-4o-2024-05-13")  # gpt-3.5-turbo-0125

mini_agents = MiniAgents()


@mini_agents.on_persist_message
async def persist_message(_, message: Message) -> None:
    """
    TODO Oleksandr: docstring
    """
    print("HASH KEY:", message.hash_key)
    print(type(message).__name__)
    pprint(message.serialize(), width=119)
    print()


async def main() -> None:
    """
    Send a message to Claude and print the response.
    """
    async with mini_agents:
        reply_sequence = llm_agent.inquire(
            "How are you today?",
            max_tokens=1000,
            temperature=0.0,
            system="Respond only in Yoda-speak.",
        )

        print()
        async for msg_promise in reply_sequence:
            async for token in msg_promise:
                print(f"\033[92;1m{token}\033[0m", end="", flush=True)
            print()
            print()


if __name__ == "__main__":
    asyncio.run(main())
