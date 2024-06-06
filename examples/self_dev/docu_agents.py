"""
This module contains MiniAgents that specialize in producing documentation for the MiniAgents framework.
"""

import asyncio
import logging
from pathlib import Path
from typing import Union

from examples.self_dev.self_dev_common import FullRepoMessage, MODEL_AGENTS, SELF_DEV_OUTPUT
from examples.self_dev.self_dev_prompts import GLOBAL_SYSTEM_HEADER, PRODUCE_README_SYSTEM_FOOTER
from miniagents.ext.llm.llm_common import SystemMessage
from miniagents.miniagents import miniagent, MiniAgents, InteractionContext


@miniagent
async def echo_agent(ctx: InteractionContext, color: Union[str, int] = "92;1") -> None:
    """
    MiniAgent that echoes messages to the console token by token.
    """
    ctx.reply(ctx.messages)  # pass the same messages forward

    async for msg_promise in ctx.messages:
        async for token in msg_promise:
            print(f"\033[{color};1m{token}\033[0m", end="", flush=True)
        print()
        print()


@miniagent
async def file_agent(ctx: InteractionContext, file: str) -> None:
    """
    MiniAgent that writes messages to a file.
    """
    ctx.reply(ctx.messages)  # pass the same messages forward

    file = Path(file)
    file.parent.mkdir(parents=True, exist_ok=True)

    with file.open("w", encoding="utf-8") as file_stream:
        async for readme_token in ctx.messages.as_single_promise():
            file_stream.write(readme_token)


@miniagent
async def readme_agent(_) -> None:  # TODO Oleksandr: make it possible not to specify `_` in the signature ?
    """
    MiniAgent that produces variants of README using different large language models.
    """
    inpt = [
        SystemMessage(GLOBAL_SYSTEM_HEADER),
        FullRepoMessage(),
        SystemMessage(PRODUCE_README_SYSTEM_FOOTER),
    ]

    # start all model agents in parallel
    for idx, (model, model_agent) in enumerate(MODEL_AGENTS.items()):
        echo_agent.inquire(
            file_agent.inquire(
                model_agent.inquire(
                    inpt,
                    temperature=0,
                ),
                file=str(SELF_DEV_OUTPUT / f"README-{model}.md"),
            ),
            color=f"{92 + idx};1",
        )

    # await ctx.await_children()  # TODO Oleksandr: support this feature


async def amain() -> None:
    """
    Main function that runs the agents.
    """
    async with MiniAgents():
        readme_agent.inquire()
    print("Readme file(s) produced")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # logging.getLogger("miniagents.ext.llm").setLevel(logging.DEBUG)

    asyncio.run(amain())
