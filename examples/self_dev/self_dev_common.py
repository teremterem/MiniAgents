"""
This module contains common code for the self-developer example.
"""

from functools import partial
from pathlib import Path

from dotenv import load_dotenv
from pydantic._internal._model_construction import ModelMetaclass

from miniagents.ext.llm.anthropic import create_anthropic_agent
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.messages import Message

load_dotenv()

MODEL_AGENT_FACTORIES = {
    "gpt-4o-2024-05-13": create_openai_agent,
    "claude-3-opus-20240229": partial(create_anthropic_agent, max_tokens=2000),
    # "claude-3-haiku-20240307": partial(create_anthropic_agent, max_tokens=2000),
}
MODEL_AGENTS = {model: factory(model=model) for model, factory in MODEL_AGENT_FACTORIES.items()}

SELF_DEV_ROOT = Path(__file__).parent
MINIAGENTS_ROOT = SELF_DEV_ROOT.parent.parent

SELF_DEV_TRANSIENT = SELF_DEV_ROOT / "transient"
SELF_DEV_OUTPUT = SELF_DEV_ROOT / "output"


class RepoFileMessage(Message):
    """
    A message that represents a file in the MiniAgents repository.
    """

    file_posix_path: str

    def _as_string(self) -> str:
        snippet_type = "python" if self.file_posix_path.endswith(".py") else ""
        extra_newline = "" if self.text.endswith("\n") else "\n"
        return f"{self.file_posix_path}\n```{snippet_type}\n{self.text}{extra_newline}```"


class ModelSingletonMeta(ModelMetaclass):
    """
    A metaclass that ensures that only one instance of a Pydantic model of a certain class is created.
    """

    _instance = None

    def __call__(cls):  # , *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__call__()  # *args, **kwargs)
        return cls._instance


class FullRepoMessage(Message, metaclass=ModelSingletonMeta):
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
                        # "examples/",
                        relative_posix_path(SELF_DEV_OUTPUT),
                        relative_posix_path(SELF_DEV_TRANSIENT),
                        "htmlcov/",
                        "venv/",
                    ]
                )
                and not any(file_posix_path.endswith(suffix) for suffix in [".pyc"])
                # skip the prompt file in order not to throw off the LLM, and also skip the `poetry.lock` file
                and not (file_posix_path in ["examples/self_developer/self_dev_prompts.py", "poetry.lock"])
            )
        ]
        # TODO Oleksandr: put `examples` folder content at the end of the message ?
        miniagent_files.sort(key=lambda file_message: file_message.file_posix_path)
        super().__init__(repo_files=miniagent_files)

        full_repo_md_file = SELF_DEV_TRANSIENT / "full-repo.md"
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
    FullRepoMessage()
    print("FullRepoMessage created and saved")
