"""
This agent is a part of the self-development process. It is designed to improve the README file of the MiniAgents.
"""

from dotenv import load_dotenv

from examples.self_dev.self_dev_common import (
    MINIAGENTS_ROOT,
    MODEL_AGENTS,
    SELF_DEV_OUTPUT,
    FullRepoMessage,
    mini_agents,
)
from examples.self_dev.self_dev_prompts import SYSTEM_HERE_ARE_REPO_FILES, SYSTEM_IMPROVE_README
from miniagents import InteractionContext, Message, MessageSequencePromise, MessageTokenAppender, miniagent
from miniagents.ext import MarkdownHistoryAgent, console_user_agent, dialog_loop, file_output_agent
from miniagents.ext.llms import SystemMessage

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

    async def _report_that_file_was_written(_md_file_name: str, _model_response: MessageSequencePromise) -> None:
        await _model_response
        token_appender.append(f"{_md_file_name}\n")

    with MessageTokenAppender() as token_appender:
        ctx.reply(Message.promise(message_token_streamer=token_appender))

        token_appender.append(f"Generating {len(MODEL_AGENTS)} variants of README.md\n\n")

        # start all model agents in parallel
        for model, model_agent in MODEL_AGENTS.items():
            md_file_name = f"README__{model}.md"

            model_response = file_output_agent.inquire(
                model_agent.inquire(prompt),
                file=str(MINIAGENTS_ROOT / md_file_name),
            )
            ctx.wait_for(_report_that_file_was_written(md_file_name, model_response))

        await ctx.await_for_subtasks()

        token_appender.append("\nALL DONE")


async def main() -> None:
    """
    The main conversation loop.
    """
    dialog_loop.kick_off(
        user_agent=console_user_agent.fork(
            history_agent=MarkdownHistoryAgent.fork(history_md_file=SELF_DEV_OUTPUT / f"CHAT__{readme_agent.alias}.md")
        ),
        assistant_agent=readme_agent,
    )


if __name__ == "__main__":
    mini_agents.run(main())
