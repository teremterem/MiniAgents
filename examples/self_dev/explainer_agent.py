"""
This agent is a part of the self-development process. It is designed to explain the MiniAgents framework to the user.
"""

import asyncio

from dotenv import load_dotenv

from examples.self_dev.self_dev_common import (
    MODEL_AGENTS,
    FullRepoMessage,
    mini_agents,
    SELF_DEV_OUTPUT,
    prompt_logger_agent,
    PROMPT_LOG_PATH_PREFIX,
)
from examples.self_dev.self_dev_prompts import SYSTEM_HERE_ARE_REPO_FILES
from miniagents import miniagent, InteractionContext
from miniagents.ext import dialog_loop, markdown_history_agent, console_user_agent
from miniagents.ext.llm import SystemMessage

load_dotenv()


@miniagent
async def explainer_agent(ctx: InteractionContext) -> None:
    """
    The job of this agent is to answer questions about the MiniAgents framework.
    """
    prompt = [
        SystemMessage(SYSTEM_HERE_ARE_REPO_FILES),
        FullRepoMessage(),
        ctx.message_promises,
    ]
    await prompt_logger_agent.inquire(prompt, history_md_file=f"{PROMPT_LOG_PATH_PREFIX}{ctx.this_agent.alias}.md")

    favourite_model = "claude-3-5-sonnet-20240620"

    other_tasks = []
    for model, model_agent in MODEL_AGENTS.items():
        if model == favourite_model:
            ctx.reply(model_agent.inquire(prompt))
        else:
            other_tasks.append(
                markdown_history_agent.inquire(
                    model_agent.inquire(prompt),
                    file=str(SELF_DEV_OUTPUT / f"ALT__{ctx.this_agent.alias}__{model}.md"),
                    only_write=True,
                )
            )

    # TODO Oleksandr: instead of having to "gather" these tasks, make sure all spawned tasks are awaited before the
    #  agent exits ? no, that would be a disaster, you need something else
    await asyncio.gather(*other_tasks, return_exceptions=True)


async def main() -> None:
    """
    The main conversation loop.
    """
    await dialog_loop.fork(
        user_agent=console_user_agent.fork(
            history_agent=markdown_history_agent.fork(
                history_md_file=SELF_DEV_OUTPUT / f"CHAT__{explainer_agent.alias}.md"
            )
        ),
        assistant_agent=explainer_agent,
    ).inquire()


if __name__ == "__main__":
    mini_agents.run(main())
