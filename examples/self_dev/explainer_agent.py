"""
This agent is a part of the self-development process. It is designed to explain the MiniAgents framework to the user.
"""

from dotenv import load_dotenv

from examples.self_dev.self_dev_common import (
    FAVOURITE_MODEL,
    MODEL_AGENTS,
    SELF_DEV_OUTPUT,
    FullRepoMessage,
    mini_agents,
)
from examples.self_dev.self_dev_llama_index import llama_index_rag_agent
from examples.self_dev.self_dev_prompts import SYSTEM_HERE_ARE_REPO_FILES
from miniagents import InteractionContext, MiniAgent, miniagent
from miniagents.ext import MarkdownHistoryAgent, console_user_agent, dialog_loop
from miniagents.ext.llms import SystemMessage

load_dotenv()


@miniagent
async def full_repo_agent(ctx: InteractionContext, llm_agent: MiniAgent) -> None:
    """
    This agent uses ALL the files in the repository to answer the user's question.
    """
    ctx.reply(
        llm_agent.trigger(
            [
                SystemMessage(SYSTEM_HERE_ARE_REPO_FILES),
                FullRepoMessage(),
                ctx.message_promises,
            ]
        )
    )


LLMS_FOR_EXPLAINER = {}
for model_ in [
    FAVOURITE_MODEL,
]:
    agent_ = MODEL_AGENTS[model_]
    LLMS_FOR_EXPLAINER[model_] = full_repo_agent.fork(llm_agent=agent_)
    LLMS_FOR_EXPLAINER[f"{model_}-RAG"] = llama_index_rag_agent.fork(llm_agent=agent_)


@miniagent
async def explainer_agent(ctx: InteractionContext) -> None:
    """
    The job of this agent is to answer questions about the MiniAgents framework.
    """
    # pylint: disable=duplicate-code
    for model, model_agent in LLMS_FOR_EXPLAINER.items():
        if model == FAVOURITE_MODEL:
            ctx.reply(model_agent.trigger(ctx.message_promises))
        else:
            ctx.make_sure_to_wait(  # let's not "close" the agent's reply sequence until the call below finishes too
                MarkdownHistoryAgent.trigger(
                    model_agent.trigger(ctx.message_promises),
                    history_md_file=str(SELF_DEV_OUTPUT / f"ALT__{ctx.this_agent.alias}__{model}.md"),
                )
            )


async def main() -> None:
    """
    The main conversation loop.
    """
    dialog_loop.trigger(
        user_agent=console_user_agent.fork(
            history_agent=MarkdownHistoryAgent.fork(
                history_md_file=str(SELF_DEV_OUTPUT / f"CHAT__{explainer_agent.alias}.md")
            )
        ),
        assistant_agent=explainer_agent,
    )


if __name__ == "__main__":
    mini_agents.run(main())
