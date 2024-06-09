"""
This module contains MiniAgents that specialize in producing documentation for the MiniAgents framework.
"""

import asyncio
import logging
from pathlib import Path
from typing import Union

from examples.self_dev.self_dev_common import MODEL_AGENTS, SELF_DEV_OUTPUT, SKIPS_FOR_REPO_VARIATIONS, FullRepoMessage
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
    experiment_name = input("\nEnter experiment folder name: ")
    experiment_name = "_".join(experiment_name.lower().split())
    if not experiment_name:
        experiment_name = "DEFAULT"

    # try all repo variations simultaneously
    for variation_idx, (variation_name, variation_skips) in enumerate(SKIPS_FOR_REPO_VARIATIONS.items()):

        # TODO Oleksandr: implement LLM agent throttling

        # start all model agents in parallel
        for model_idx, (model, model_agent) in enumerate(MODEL_AGENTS.items()):

            md_file = SELF_DEV_OUTPUT / f"README__{experiment_name}__{variation_name}__{model}.md"

            if md_file.exists() and md_file.stat().st_size > 0 and md_file.read_text(encoding="utf-8").strip():
                continue

            echo_agent.inquire(
                file_agent.inquire(
                    model_agent.inquire(
                        [
                            SystemMessage(GLOBAL_SYSTEM_HEADER),
                            FullRepoMessage(
                                experiment_name=experiment_name,
                                variation_name=variation_name,
                                skip_if_starts_with=variation_skips,
                            ),
                            SystemMessage(PRODUCE_README_SYSTEM_FOOTER),
                        ],
                        temperature=0,
                    ),
                    file=str(md_file),
                ),
                color=f"{90 + len(MODEL_AGENTS) * variation_idx + model_idx};1",
            )

    # TODO Oleksandr: support this feature
    # await ctx.await_children()


async def amain() -> None:
    """
    Main function that runs the agents.
    """
    async with MiniAgents():
        readme_agent.inquire()
    print("Readme file(s) produced\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("miniagents.ext.llm").setLevel(logging.DEBUG)

    asyncio.run(amain())
