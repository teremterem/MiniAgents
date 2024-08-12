"""
A conversation example between the user and multiple LLMs using the MiniAgents framework.
"""

import sys
from pathlib import Path
from typing import Union

from dotenv import load_dotenv

from miniagents import InteractionContext, MiniAgents, miniagent
from miniagents.ext import MarkdownHistoryAgent, console_user_agent, dialog_loop
from miniagents.ext.agents.history_agents import markdown_llm_logger_agent
from miniagents.ext.llms.anthropic import AnthropicAgent
from miniagents.ext.llms.openai import OpenAIAgent

load_dotenv()

VERSATILIS_FOLDER = Path(".versatilis")

GPT_4O = "gpt-4o-2024-08-06"
CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20240620"

FAVOURITE_MODEL = CLAUDE_3_5_SONNET

MAX_OUTPUT_TOKENS = 4096

MODEL_AGENT_FACTORIES = {
    GPT_4O: OpenAIAgent.fork(temperature=0),
    "gpt-4-turbo-2024-04-09": OpenAIAgent.fork(temperature=0),
    "gpt-4o-mini-2024-07-18": OpenAIAgent.fork(temperature=0),
    CLAUDE_3_5_SONNET: AnthropicAgent.fork(max_tokens=MAX_OUTPUT_TOKENS, temperature=0),
    "claude-3-opus-20240229": AnthropicAgent.fork(max_tokens=MAX_OUTPUT_TOKENS, temperature=0),
    "claude-3-haiku-20240307": AnthropicAgent.fork(max_tokens=MAX_OUTPUT_TOKENS, temperature=0),
}
MODEL_AGENTS = {
    model: MODEL_AGENT_FACTORIES[model].fork(model=model)
    for model in [
        # let's use only two best models in our self_dev agents
        GPT_4O,
        CLAUDE_3_5_SONNET,
    ]
}
FAVOURITE_MODEL_AGENT = MODEL_AGENTS[FAVOURITE_MODEL]
ALT_MODEL_AGENTS = {model: MODEL_AGENTS[model] for model in MODEL_AGENTS if model != FAVOURITE_MODEL}


@miniagent
async def versatilis(
    ctx: InteractionContext,
) -> None:
    """
    This agent employs many models to answer to the user. The answers of the "favourite" model are considered part of
    the "official" chat history, while the answers of the other models are just written to separate markdown files.
    """
    ctx.reply(FAVOURITE_MODEL_AGENT.inquire(ctx.message_promises))

    for idx, (model, model_agent) in enumerate(ALT_MODEL_AGENTS.items()):
        console_style = "36;1" if idx % 2 == 0 else None
        ctx.reply(
            MarkdownHistoryAgent.inquire(
                model_agent.inquire(
                    ctx.message_promises,
                    response_metadata={
                        # the "no_history" flag is for the global history agent that writes to CHAT.md
                        "no_history": True,
                        # the "console_style" flag is for the `console_output_agent`
                        "console_style": console_style,
                    },
                ),
                history_md_file=str(VERSATILIS_FOLDER / f"ALT__{model}.md"),
                ignore_no_history=True,  # the local history agent should still write the ignored messages to the file
            )
        )


async def amain(file_path: Union[str, Path, None] = None) -> None:
    """
    The main conversation loop.
    """
    if file_path:
        file_path = Path(file_path)
        prompt = file_path.read_text(encoding="utf-8")
        print()
        print(prompt)
    else:
        prompt = None

    dialog_loop.kick_off(
        prompt,
        user_agent=console_user_agent.fork(
            # write chat history to a markdown file
            history_agent=MarkdownHistoryAgent.fork(history_md_file=str(VERSATILIS_FOLDER / "CHAT.md"))
        ),
        assistant_agent=versatilis,
    )


def main() -> None:
    """
    The main conversation loop.
    """
    file_path = sys.argv[1] if len(sys.argv) > 1 else None

    MiniAgents(llm_logger_agent=markdown_llm_logger_agent.fork(log_folder=str(VERSATILIS_FOLDER / "llm_logs"))).run(
        amain(file_path=file_path)
    )


if __name__ == "__main__":
    main()
