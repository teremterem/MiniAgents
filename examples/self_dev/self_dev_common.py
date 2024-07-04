"""
This module contains common `self_def` code.
"""

from pathlib import Path

from dotenv import load_dotenv

from miniagents import MiniAgents, Message
from miniagents.ext import markdown_llm_logger_agent
from miniagents.ext.llm import AnthropicAgent, OpenAIAgent

load_dotenv()

MAX_OUTPUT_TOKENS = 4096

MODEL_AGENT_FACTORIES = {
    "gpt-4o-2024-05-13": OpenAIAgent.fork(temperature=0),
    "gpt-4-turbo-2024-04-09": OpenAIAgent.fork(temperature=0),
    "gpt-3.5-turbo-0125": OpenAIAgent.fork(temperature=0),
    "claude-3-5-sonnet-20240620": AnthropicAgent.fork(max_tokens=MAX_OUTPUT_TOKENS, temperature=0),
    "claude-3-opus-20240229": AnthropicAgent.fork(max_tokens=MAX_OUTPUT_TOKENS, temperature=0),
    "claude-3-haiku-20240307": AnthropicAgent.fork(max_tokens=MAX_OUTPUT_TOKENS, temperature=0),
}
MODEL_AGENTS = {
    model: MODEL_AGENT_FACTORIES[model].fork(model=model)
    for model in [
        # let's use only two best models in our self_dev agents
        "gpt-4o-2024-05-13",
        "claude-3-5-sonnet-20240620",
    ]
}

SELF_DEV_ROOT = Path(__file__).parent
MINIAGENTS_ROOT = SELF_DEV_ROOT.parent.parent

SELF_DEV_OUTPUT = SELF_DEV_ROOT / "output"
SELF_DEV_PROMPTS = SELF_DEV_ROOT / "self_dev_prompts.py"
SELF_DEV_LLM_LOGS = SELF_DEV_ROOT / "llm_logs"

mini_agents = MiniAgents(llm_logger_agent=markdown_llm_logger_agent.fork())


class RepoFileMessage(Message):
    """
    A message that represents a file in the MiniAgents repository.
    """

    file_posix_path: str

    def _as_string(self) -> str:
        extra_newline = "" if self.text.endswith("\n") else "\n"
        return f'<source_file path="{self.file_posix_path}">\n{self.text}{extra_newline}</source_file>'


class FullRepoMessage(Message):
    """
    A message that represents the full content of the MiniAgents repository.
    """

    repo_files: tuple[RepoFileMessage, ...]

    def __init__(self) -> None:
        """
        Create a FullRepoMessage object that contains the full content of the MiniAgents repository. (Take a snapshot
        of the files as they currently are, in other words.)
        """
        miniagent_files = [
            (relative_posix_path(file), file)
            for file in MINIAGENTS_ROOT.rglob("*")
            if file.is_file() and file.stat().st_size > 0
        ]
        miniagent_files = [
            RepoFileMessage(file_posix_path=file_posix_path, text=file.read_text(encoding="utf-8"))
            for file_posix_path, file in miniagent_files
            if (
                not any(
                    file_posix_path.startswith(prefix)
                    for prefix in [
                        ".",
                        "dist/",
                        relative_posix_path(SELF_DEV_LLM_LOGS),
                        relative_posix_path(SELF_DEV_OUTPUT),
                        # relative_posix_path(SELF_DEV_PROMPTS),  # TODO Oleksandr: skip the prompts file ?
                        "htmlcov/",
                        "images/",
                        # "LICENSE",
                        "venv/",
                        "poetry.lock",
                    ]
                )
                and not any(file_posix_path.endswith(suffix) for suffix in [".pyc"])
            )
        ]
        miniagent_files.sort(key=lambda file_message: file_message.file_posix_path)
        super().__init__(repo_files=miniagent_files)

    def _as_string(self) -> str:
        file_list_str = "\n".join([file_message.file_posix_path for file_message in self.repo_files])
        source_files_str = "\n\n\n\n".join([str(file_message) for file_message in self.repo_files])
        return f"<file_list>\n{file_list_str}\n</file_list>\n\n\n\n<files>\n{source_files_str}\n</files>"


def relative_posix_path(file: Path) -> str:
    """
    Get the path of a file as a POSIX path relative to the MiniAgents repository root.
    """
    return file.relative_to(MINIAGENTS_ROOT).as_posix()
