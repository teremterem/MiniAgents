# pylint: disable=wrong-import-position
"""
Code example for using Anthropic Claude.
"""

import asyncio

# noinspection PyUnresolvedReferences
import readline  # pylint: disable=unused-import
from pprint import pprint

from dotenv import load_dotenv

load_dotenv()

from miniagents.ext.llms.anthropic import create_anthropic_agent
from miniagents.promisegraph.promise import PromiseContext

anthropic_agent = create_anthropic_agent()


async def main() -> None:
    """
    Send a message to Claude and print the response.
    """
    async with PromiseContext():
        reply_sequence = anthropic_agent.inquire(
            "How are you today?",
            model="claude-3-haiku-20240307",  # "claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0.0,
            system="Respond only in Yoda-speak.",
            stream=True,
        )

        print()
        async for msg_promise in reply_sequence:
            async for token in msg_promise:
                print(token, end="", flush=True)
            print()
            print()
            pprint((await msg_promise.acollect()).model_dump())
        print()


if __name__ == "__main__":
    asyncio.run(main())
