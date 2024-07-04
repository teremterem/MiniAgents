"""
This agent is a part of the self-development process. It is designed to explain the MiniAgents framework to the user.
"""

from dotenv import load_dotenv

from examples.self_dev.self_dev_common import (
    MODEL_AGENTS,
    FullRepoMessage,
    mini_agents,
    SELF_DEV_OUTPUT,
)
from examples.self_dev.self_dev_prompts import SYSTEM_HERE_ARE_REPO_FILES
from miniagents import miniagent, InteractionContext
from miniagents.ext import dialog_loop, MarkdownHistoryAgent, console_user_agent
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

    favourite_model = "claude-3-5-sonnet-20240620"

    for model, model_agent in MODEL_AGENTS.items():
        if model == favourite_model:
            ctx.reply(model_agent.inquire(prompt))
        else:
            ctx.wait_for(  # let's not "close" the agent's reply sequence until the [sub]agent below finishes too
                MarkdownHistoryAgent.inquire(
                    model_agent.inquire(prompt),
                    history_md_file=str(SELF_DEV_OUTPUT / f"ALT__{ctx.this_agent.alias}__{model}.md"),
                    only_write=True,
                )
            )


async def main() -> None:
    """
    The main conversation loop.
    """
    dialog_loop.fork(
        user_agent=console_user_agent.fork(
            history_agent=MarkdownHistoryAgent.fork(
                history_md_file=SELF_DEV_OUTPUT / f"CHAT__{explainer_agent.alias}.md"
            )
        ),
        assistant_agent=explainer_agent,
    ).kick_off()


if __name__ == "__main__":
    mini_agents.run(main())
