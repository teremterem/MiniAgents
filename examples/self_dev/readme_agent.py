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
from examples.self_dev.self_dev_prompts import SYSTEM_HERE_ARE_REPO_FILES, SYSTEM_IMPROVE_README
from miniagents.ext.agent_aggregators import dialog_loop
from miniagents.ext.history_agents import markdown_history_agent
from miniagents.ext.llm.llm_common import SystemMessage
from miniagents.ext.misc_agents import file_agent
from miniagents.messages import Message, MessageSequencePromise
from miniagents.miniagents import miniagent, InteractionContext
from miniagents.promising.promising import StreamAppender

load_dotenv()


@miniagent
async def readme_agent(ctx: InteractionContext) -> None:
    """
    The job of this agent is to improve the README files of the MiniAgents repository based on the conversation
    with the user.
    """
    prompt = [
        SystemMessage(SYSTEM_HERE_ARE_REPO_FILES),
        FullRepoMessage(),
        SystemMessage(SYSTEM_IMPROVE_README),
        ctx.message_promises,
    ]
    markdown_history_agent.inquire(
        prompt,
        history_md_file=str(SELF_DEV_TRANSIENT / "FULL_PROMPT.md"),
        default_role="user",
        only_write=True,
        append=False,
    )

    token_appender = StreamAppender[str]()
    ctx.reply(Message.promise(message_token_streamer=token_appender))

    async def _report_file_written(_md_file_name: str, _model_response: MessageSequencePromise) -> None:
        await _model_response
        token_appender.append(f"{_md_file_name}\n")

    with token_appender:
        token_appender.append(f"Generating {len(MODEL_AGENTS)} variants of README.md\n\n")

        report_tasks = []
        # start all model agents in parallel
        for model, model_agent in MODEL_AGENTS.items():
            md_file_name = f"README__{model}.md"

            model_response = file_agent.inquire(
                model_agent.inquire(prompt, temperature=0),
                file=str(MINIAGENTS_ROOT / md_file_name),
            )
            report_tasks.append(mini_agents.start_asap(_report_file_written(md_file_name, model_response)))

        # TODO Oleksandr: instead of having to "gather" these tasks, make sure all spawned tasks are awaited before the
        #  agent exits ? no, that would be a disaster, you need something else
        await asyncio.gather(*report_tasks, return_exceptions=True)

        token_appender.append("\nALL DONE")


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
