"""
Make all the agents from the `agents` package available at the level of the `ext` package.
"""

from miniagents.ext.agents.agent_aggregators import (
    agent_chain,
    agent_loop,
    console_user_agent,
    dialog_loop,
    user_agent,
)
from miniagents.ext.agents.history_agents import (
    in_memory_history_agent,
    MarkdownHistoryAgent,
    markdown_llm_logger_agent,
)
from miniagents.ext.agents.misc_agents import (
    console_input_agent,
    console_output_agent,
    file_output_agent,
)

__all__ = [
    "agent_chain",
    "agent_loop",
    "console_input_agent",
    "console_output_agent",
    "console_user_agent",
    "dialog_loop",
    "file_output_agent",
    "in_memory_history_agent",
    "MarkdownHistoryAgent",
    "markdown_llm_logger_agent",
    "user_agent",
]
