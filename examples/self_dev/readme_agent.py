"""
This agent is a part of the self-development process. It is designed to improve the README file of the MiniAgents.
"""

import asyncio

from dotenv import load_dotenv

from examples.self_dev.self_dev_common import (
    MINIAGENTS_ROOT,
    MODEL_AGENTS,
    FullRepoMessage,
    mini_agents,
    SELF_DEV_OUTPUT,
    prompt_logger_agent,
    PROMPT_LOG_PATH_PREFIX,
)
from examples.self_dev.self_dev_prompts import SYSTEM_HERE_ARE_REPO_FILES, SYSTEM_IMPROVE_README
from miniagents import miniagent, InteractionContext, StreamAppender, Message, MessageSequencePromise
from miniagents.ext import file_agent, dialog_loop, MarkdownHistoryAgent, console_user_agent
from miniagents.ext.llm import SystemMessage

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
    await prompt_logger_agent.inquire(prompt, history_md_file=f"{PROMPT_LOG_PATH_PREFIX}{ctx.this_agent.alias}.md")

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
                model_agent.inquire(prompt),
                file=str(MINIAGENTS_ROOT / md_file_name),
            )
            report_tasks.append(mini_agents.start_asap(_report_file_written(md_file_name, model_response)))

        # TODO Oleksandr: instead of having to "gather" these tasks, make sure all spawned tasks are awaited before the
        #  agent exits ? no, that would be a disaster, you need something else
        await asyncio.gather(*report_tasks, return_exceptions=True)

        token_appender.append("\nALL DONE")


async def main() -> None:
    """
    The main conversation loop.
    """
    await dialog_loop.fork(
        user_agent=console_user_agent.fork(
            history_agent=MarkdownHistoryAgent.fork(history_md_file=SELF_DEV_OUTPUT / f"CHAT__{readme_agent.alias}.md")
        ),
        assistant_agent=readme_agent,
    ).inquire()


if __name__ == "__main__":
    mini_agents.run(main())
