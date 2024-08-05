"""
This module contains common `self_def` code.
"""

from pathlib import Path

from dotenv import load_dotenv

from miniagents import Message, MiniAgents, cached_privately
from miniagents.ext import markdown_llm_logger_agent
from miniagents.ext.llms import AnthropicAgent, OpenAIAgent
from miniagents.utils import ModelSingleton

load_dotenv()

GPT_4O = "gpt-4o-2024-05-13"
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

SELF_DEV_ROOT = Path(__file__).parent
MINIAGENTS_ROOT = SELF_DEV_ROOT.parent.parent

SELF_DEV_OUTPUT = MINIAGENTS_ROOT / "self_def_output"
SELF_DEV_PROMPTS = SELF_DEV_ROOT / "self_dev_prompts.py"
LLM_LOGS = MINIAGENTS_ROOT / "llm_logs"
TRANSIENT = MINIAGENTS_ROOT / "transient"

mini_agents = MiniAgents(llm_logger_agent=markdown_llm_logger_agent.fork(log_folder=str(LLM_LOGS)))


class RepoFileMessage(Message):
    """
    A message that represents a file in the MiniAgents repository.
    """

    file_posix_path: str

    @property
    @cached_privately
    def lazy_content(self):
        """
        A lazy property that returns the content of the file.
        """
        return (MINIAGENTS_ROOT / self.file_posix_path).read_text(encoding="utf-8")

    @property
    @cached_privately
    def num_of_newlines(self):
        """
        The number of newlines in the content of the file.
        """
        return self.lazy_content.count("\n")

    def _as_string(self) -> str:
        extra_newline = "" if self.lazy_content.endswith("\n") else "\n"
        return f'<source_file path="{self.file_posix_path}">\n{self.lazy_content}{extra_newline}</source_file>'


class FullRepoMessage(Message, ModelSingleton):
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
            RepoFileMessage(file_posix_path=file_posix_path)
            for file_posix_path, file in miniagent_files
            if (
                not any(
                    file_posix_path.startswith(prefix)
                    for prefix in [
                        ".",
                        "dist/",
                        # relative_posix_path(SELF_DEV_PROMPTS),  # TODO Oleksandr: skip the prompts file ?
                        "htmlcov/",
                        "images/",
                        # "LICENSE",
                        relative_posix_path(LLM_LOGS),
                        "venv/",
                        "poetry.lock",
                        relative_posix_path(SELF_DEV_OUTPUT),
                        relative_posix_path(TRANSIENT),
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
