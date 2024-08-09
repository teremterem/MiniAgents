"""
A conversation example between the user and multiple LLMs using the MiniAgents framework.
"""

import sys
from pathlib import Path
from typing import Union

from dotenv import load_dotenv

from examples.self_dev.self_dev_common import FAVOURITE_MODEL, MODEL_AGENTS
from miniagents import InteractionContext, MiniAgents, miniagent
from miniagents.ext import MarkdownHistoryAgent, console_user_agent, dialog_loop
from miniagents.ext.agents.history_agents import markdown_llm_logger_agent

load_dotenv()

VERSATILIS_FOLDER = Path(".versatilis")


@miniagent
async def versatilis(
    ctx: InteractionContext,
) -> None:
    """
    This agent employs many models to answer to the user. The answers of the "favourite" model are considered part of
    the "official" chat history, while the answers of the other models are just written to separate markdown files.
    """
    ctx.reply(MODEL_AGENTS[FAVOURITE_MODEL].inquire(ctx.message_promises))

    for model, model_agent in MODEL_AGENTS.items():
        if model == FAVOURITE_MODEL:
            continue

        ctx.reply(
            MarkdownHistoryAgent.inquire(
                model_agent.inquire(
                    ctx.message_promises,
                    response_metadata={
                        # this flag is for the main history agent that writes to CHAT.md
                        "no_history": True,
                    },
                ),
                history_md_file=str(VERSATILIS_FOLDER / f"ALT__{model}.md"),
                ignore_no_history=True,  # the local history agent should still write the ignored messages to the file
            )
        )


async def main(file_path: Union[str, None] = None) -> None:
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


if __name__ == "__main__":
    _file_path = sys.argv[1] if len(sys.argv) > 1 else None
    MiniAgents(llm_logger_agent=markdown_llm_logger_agent.fork(log_folder=str(VERSATILIS_FOLDER / "llm_logs"))).run(
        main(file_path=_file_path)
    )
