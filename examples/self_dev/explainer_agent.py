"""
This agent is a part of the self-development process. It is designed to explain the MiniAgents framework to the user.
"""

from dotenv import load_dotenv

from examples.self_dev.self_dev_common import (
    MODEL_AGENTS,
    FullRepoMessage,
    mini_agents,
    SELF_DEV_OUTPUT,
    FAVOURITE_MODEL,
)
from examples.self_dev.self_dev_llama_index import llama_index_rag_agent
from examples.self_dev.self_dev_prompts import SYSTEM_HERE_ARE_REPO_FILES
from miniagents import miniagent, InteractionContext, MiniAgent
from miniagents.ext import dialog_loop, MarkdownHistoryAgent, console_user_agent
from miniagents.ext.llms import SystemMessage

load_dotenv()


@miniagent
async def full_repo_agent(ctx: InteractionContext, llm_agent: MiniAgent) -> None:
    """
    This agent uses ALL the files in the repository to answer the user's question.
    """
    ctx.reply(
        llm_agent.inquire(
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
    for model, model_agent in LLMS_FOR_EXPLAINER.items():
        if model == FAVOURITE_MODEL:
            ctx.reply(model_agent.inquire(ctx.message_promises))
        else:
            ctx.wait_for(  # let's not "close" the agent's reply sequence until the agent call below finishes too
                MarkdownHistoryAgent.inquire(
                    model_agent.inquire(ctx.message_promises),
                    history_md_file=str(SELF_DEV_OUTPUT / f"ALT__{ctx.this_agent.alias}__{model}.md"),
                    only_write=True,
                )
            )


async def main() -> None:
    """
    The main conversation loop.
    """
    dialog_loop.kick_off(
        user_agent=console_user_agent.fork(
            history_agent=MarkdownHistoryAgent.fork(
                history_md_file=str(SELF_DEV_OUTPUT / f"CHAT__{explainer_agent.alias}.md")
            )
        ),
        assistant_agent=explainer_agent,
    )


if __name__ == "__main__":
    mini_agents.run(main())
