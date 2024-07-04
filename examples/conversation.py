"""
A conversation example between the user and multiple LLMs using the MiniAgents framework.
"""

from dotenv import load_dotenv

from examples.self_dev.self_dev_common import MODEL_AGENT_FACTORIES
from miniagents import MiniAgents, InteractionContext, miniagent
from miniagents.ext import dialog_loop, MarkdownHistoryAgent, console_user_agent

load_dotenv()

MODEL_AGENTS = {model: agent.fork(model=model) for model, agent in MODEL_AGENT_FACTORIES.items()}


@miniagent
async def all_models_agent(ctx: InteractionContext) -> None:
    """
    This agent employs many models to answer to the user. The answers of the "favourite" model are considered part of
    the "official" chat history, while the answers of the other models are just written to separate markdown files.
    """
    favourite_model = "claude-3-5-sonnet-20240620"

    for model, model_agent in MODEL_AGENTS.items():
        if model == favourite_model:
            ctx.reply(model_agent.inquire(ctx.message_promises))
        else:
            ctx.wait_for(  # let's not "close" the agent's reply sequence until the [sub]agent below finishes too
                MarkdownHistoryAgent.inquire(
                    model_agent.inquire(ctx.message_promises),
                    history_md_file=f"ALT__{model}.md",
                    only_write=True,
                )
            )


async def main() -> None:
    """
    The main conversation loop.
    """
    dialog_loop.fork(
        user_agent=console_user_agent.fork(
            # write chat history to a markdown file
            history_agent=MarkdownHistoryAgent
        ),
        assistant_agent=all_models_agent,
    ).kick_off()


if __name__ == "__main__":
    MiniAgents().run(main())
