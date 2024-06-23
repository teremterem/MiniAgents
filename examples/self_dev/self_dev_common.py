"""
This module contains common code for the self-developer example.
"""

from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv

from miniagents.ext.llm.anthropic import anthropic_agent
from miniagents.ext.llm.openai import openai_agent
from miniagents.messages import Message

load_dotenv()

MODEL_AGENT_FACTORIES = {
    "gpt-4o-2024-05-13": openai_agent,
    "claude-3-5-sonnet-20240620": anthropic_agent.fork(max_tokens=2000),
    "claude-3-opus-20240229": anthropic_agent.fork(max_tokens=2000),
    "claude-3-haiku-20240307": anthropic_agent.fork(max_tokens=2000),
}
MODEL_AGENTS = {model: agent.fork(model=model) for model, agent in MODEL_AGENT_FACTORIES.items()}

SELF_DEV_ROOT = Path(__file__).parent
MINIAGENTS_ROOT = SELF_DEV_ROOT.parent.parent

SELF_DEV_OUTPUT = SELF_DEV_ROOT / "output"
SELF_DEV_PROMPTS = SELF_DEV_ROOT / "self_dev_prompts.py"
SELF_DEV_TRANSIENT = SELF_DEV_ROOT / "transient"


class RepoFileMessage(Message):
    """
    A message that represents a file in the MiniAgents repository.
    """

    file_posix_path: str

    def _as_string(self) -> str:
        snippet_type = "python" if self.file_posix_path.endswith(".py") else ""
        extra_newline = "" if self.text.endswith("\n") else "\n"
        return f"{self.file_posix_path}\n```{snippet_type}\n{self.text}{extra_newline}```"


SKIPS_FOR_REPO_VARIATIONS: dict[str, list[str]] = {
    "complete": [],
    # "no_pypr": ["pyproject.toml"],
    # "no_pypr_no_readme": ["pyproject.toml", "README.md"],
    # "no_pypr_no_readme_no_examples": ["pyproject.toml", "README.md", "examples/"],
    # "no_pypr_no_readme_no_examples_no_tests": ["pyproject.toml", "README.md", "examples/", "tests/"],
}


class FullRepoMessage(Message):  # TODO Oleksandr: bring back `ModelSingleton` ?
    """
    A message that represents the full content of the MiniAgents repository.
    """

    variation_name: str
    repo_files: tuple[RepoFileMessage, ...]

    def __init__(self, experiment_name: str, variation_name: str, skip_if_starts_with: Iterable[str] = ()) -> None:
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
                        relative_posix_path(SELF_DEV_OUTPUT),
                        # relative_posix_path(SELF_DEV_PROMPTS),  # skip prompt file in order not to throw LLM off ?
                        relative_posix_path(SELF_DEV_TRANSIENT),
                        "htmlcov/",
                        "LICENSE",  # TODO Oleksandr: what if there is a `LICENSE-template` file, for ex. ?
                        "venv/",
                        "poetry.lock",
                        *skip_if_starts_with,
                    ]
                )
                and not any(file_posix_path.endswith(suffix) for suffix in [".pyc"])
            )
        ]
        miniagent_files.sort(key=lambda file_message: file_message.file_posix_path)
        super().__init__(repo_files=miniagent_files, variation_name=variation_name)

        full_repo_md_file = SELF_DEV_TRANSIENT / f"REPO__{experiment_name}__{variation_name}.md"
        full_repo_md_file.parent.mkdir(parents=True, exist_ok=True)
        full_repo_md_file.write_text(str(self), encoding="utf-8")

    def _as_string(self) -> str:
        miniagent_files_str = "\n".join([file_message.file_posix_path for file_message in self.repo_files])

        return "\n\n\n\n".join(
            [
                f"File list:\n```\n{miniagent_files_str}\n```",
                *[str(file_message) for file_message in self.repo_files],
            ]
        )


def relative_posix_path(file: Path) -> str:
    """
    Get the path of a file as a POSIX path relative to the MiniAgents repository root.
    """
    return file.relative_to(MINIAGENTS_ROOT).as_posix()


if __name__ == "__main__":
    FullRepoMessage(experiment_name="test", variation_name="complete")
    print("FullRepoMessage created and saved")
