"""
A conversation example between the user and multiple LLMs using the MiniAgents framework.
"""

from dotenv import load_dotenv

from miniagents import InteractionContext, MiniAgents, miniagent
from miniagents.ext import MarkdownHistoryAgent, console_user_agent, dialog_loop
from miniagents.ext.llms import AnthropicAgent, OpenAIAgent

load_dotenv()

MAX_OUTPUT_TOKENS = 4096

MODEL_AGENT_FACTORIES = {
    "gpt-4o": OpenAIAgent,
    "claude-3-7-sonnet-latest": AnthropicAgent.fork(max_tokens=MAX_OUTPUT_TOKENS),
}

MODEL_AGENTS = {model: factory.fork(model=model) for model, factory in MODEL_AGENT_FACTORIES.items()}
FAVOURITE_MODEL = list(MODEL_AGENTS)[0]  # the first model in the dictionary will be our favourite one


@miniagent
async def all_models_agent(ctx: InteractionContext) -> None:
    """
    This agent employs many models to answer to the user. The answers of the "favourite" model are considered part of
    the "official" chat history, while the answers of the other models are just written to separate markdown files.
    """
    for model, model_agent in MODEL_AGENTS.items():
        if model == FAVOURITE_MODEL:
            ctx.reply(model_agent.trigger(ctx.message_promises))
        else:
            ctx.make_sure_to_wait(  # let's not "close" the agent's reply sequence until the call below finishes too
                MarkdownHistoryAgent.trigger(
                    model_agent.trigger(ctx.message_promises),
                    history_md_file=f"ALT__{model}.md",
                )
            )


async def main() -> None:
    """
    The main conversation loop.
    """
    dialog_loop.trigger(
        user_agent=console_user_agent.fork(
            # write chat history to a markdown file
            history_agent=MarkdownHistoryAgent
        ),
        assistant_agent=all_models_agent,
    )


if __name__ == "__main__":
    MiniAgents(llm_logger_agent=True).run(main())
