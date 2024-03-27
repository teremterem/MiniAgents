# pylint: disable=wrong-import-position
"""
Code example for using Anthropic Claude.
"""

import asyncio

# noinspection PyUnresolvedReferences
import readline  # pylint: disable=unused-import

from dotenv import load_dotenv

load_dotenv()

from miniagents.ext.llms.anthropic import anthropic


async def main() -> None:
    """
    Send a message to Claude and print the response.
    """
    msg_promise = anthropic(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0.0,
        system="Respond only in Yoda-speak.",
        messages=[{"role": "user", "content": "How are you today?"}],
        stream=True,
    )

    async for token in msg_promise:
        print(token, end="", flush=True)
    print()
    print()


if __name__ == "__main__":
    asyncio.run(main())
