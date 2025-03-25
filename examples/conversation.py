"""
A conversation example between the user and multiple LLMs using the MiniAgents framework.
"""

from dotenv import load_dotenv

from examples.self_dev.self_dev_common import FAVOURITE_MODEL, MODEL_AGENTS
from miniagents import InteractionContext, MiniAgents, miniagent
from miniagents.ext import MarkdownHistoryAgent, console_user_agent, dialog_loop

load_dotenv()


@miniagent
async def all_models_agent(ctx: InteractionContext) -> None:
    """
    This agent employs many models to answer to the user. The answers of the "favourite" model are considered part of
    the "official" chat history, while the answers of the other models are just written to separate markdown files.
    """
    raise ValueError("some error")  # TODO Oleksandr: don't forget to remove this
    for model, model_agent in MODEL_AGENTS.items():
        if model == FAVOURITE_MODEL:
            ctx.reply(model_agent.inquire(ctx.message_promises))
        else:
            ctx.wait_for(  # let's not "close" the agent's reply sequence until the [sub]agent below finishes too
                MarkdownHistoryAgent.inquire(
                    model_agent.inquire(ctx.message_promises),
                    history_md_file=f"ALT__{model}.md",
                )
            )


async def main() -> None:
    """
    The main conversation loop.
    """
    dialog_loop.kick_off(
        user_agent=console_user_agent.fork(
            # write chat history to a markdown file
            history_agent=MarkdownHistoryAgent
        ),
        assistant_agent=all_models_agent,
    )


if __name__ == "__main__":
    MiniAgents(llm_logger_agent=True).run(main())
