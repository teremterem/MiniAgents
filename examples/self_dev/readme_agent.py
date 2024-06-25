"""
This agent is a part of the self-development process. It is designed to improve the README file of the MiniAgents.
"""

import asyncio
import logging

from dotenv import load_dotenv

from examples.self_dev.self_dev_common import (
    MINIAGENTS_ROOT,
    MODEL_AGENTS,
    FullRepoMessage,
    mini_agents,
    SELF_DEV_TRANSIENT,
    SELF_DEV_OUTPUT,
)
from examples.self_dev.self_dev_prompts import GLOBAL_SYSTEM_HEADER
from miniagents.ext.agent_aggregators import dialog_loop
from miniagents.ext.history_agents import markdown_history_agent
from miniagents.ext.llm.llm_common import SystemMessage
from miniagents.ext.misc_agents import file_agent
from miniagents.messages import Message, MessageSequencePromise
from miniagents.miniagents import miniagent, InteractionContext

load_dotenv()


@miniagent
async def readme_agent(ctx: InteractionContext) -> None:
    """
    The job of this agent is to improve the README files of the MiniAgents repository based on the conversation
    with the user.
    """
    prompt = [
        SystemMessage(GLOBAL_SYSTEM_HEADER),
        FullRepoMessage(),
        ctx.message_promises,
    ]
    markdown_history_agent.inquire(
        prompt, history_md_file=str(SELF_DEV_TRANSIENT / "FULL_PROMPT.md"), only_write=True, append=False
    )

    async def _report_file_written(_md_file_name: str, _model_response: MessageSequencePromise) -> None:
        await _model_response
        ctx.reply(Message(f"`{_md_file_name}` generated.", no_history=True))

    report_tasks = []
    # start all model agents in parallel
    for model, model_agent in MODEL_AGENTS.items():
        md_file_name = f"README__{model}.md"

        ctx.reply(Message(f"Generating `{md_file_name}`...", no_history=True))

        model_response = file_agent.inquire(
            model_agent.inquire(prompt, temperature=0),
            file=str(MINIAGENTS_ROOT / md_file_name),
        )
        report_tasks.append(mini_agents.start_asap(_report_file_written(md_file_name, model_response)))

    # TODO Oleksandr: instead of having to "gather" these tasks, make sure all spawned tasks are awaited before the
    #  agent exits ?
    await asyncio.gather(*report_tasks, return_exceptions=True)


async def amain() -> None:
    """
    The main conversation loop.
    """
    await dialog_loop.fork(
        assistant_agent=readme_agent,
        history_agent=markdown_history_agent.fork(history_md_file=SELF_DEV_OUTPUT / "CHAT_HISTORY.md"),
    ).inquire()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    # logging.getLogger("miniagents.ext.llm").setLevel(logging.DEBUG)

    mini_agents.run(amain())
