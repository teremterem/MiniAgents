"""
This module provides a class working with chat history stored in a markdown file.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from markdown_it import MarkdownIt

from miniagents.chat_history import ChatHistory
from miniagents.messages import Message
from miniagents.miniagents import InteractionContext


class ChatHistoryMD(ChatHistory):
    """
    Class for loading chat history from a markdown file as well as writing new messages to it.
    """

    _md = MarkdownIt()

    def __init__(self, chat_md_file: Union[str, Path], default_role: str = "assistant") -> None:
        self._chat_md_file = Path(chat_md_file)
        self._default_role = default_role

    async def _logging_agent(self, ctx: InteractionContext) -> None:
        """
        The implementation of the agent that logs the chat history to a markdown file.
        """
        with self._chat_md_file.open(
            "a",  # append mode
            buffering=1,  # line buffering
            encoding="utf-8",
        ) as chat_md_file:
            async for msg_promise in ctx.messages:
                try:
                    message_role = msg_promise.preliminary_metadata.role
                except AttributeError:
                    message_role = self._default_role
                try:
                    message_model = f" / {msg_promise.preliminary_metadata.model}"
                except AttributeError:
                    message_model = ""

                chat_md_file.write(f"\n{message_role}{message_model}\n========================================\n")

                async for token in msg_promise:
                    chat_md_file.write(token)
                chat_md_file.write("\n")

    async def aload_chat_history(self) -> tuple[Message, ...]:
        """
        Parse a markdown content as a dialog.
        TODO Oleksandr: implement exhaustive unit tests for this function
        """
        md_content = self._chat_md_file.read_text(encoding="utf-8")

        md_lines = md_content.split("\n")
        md_tokens = self._md.parse(md_content)

        last_section = None
        sections = []

        for idx, md_token in enumerate(md_tokens):
            if md_token.type != "heading_open" or md_token.tag != "h1" or md_token.level != 0:
                continue

            heading = md_tokens[idx + 1].content  # the next token is `inline` with the heading content
            heading_parts = heading.split("/", maxsplit=1)
            role = heading_parts[0].strip().lower()

            if role not in ["user", "assistant"]:
                continue

            if len(heading_parts) > 1:
                model = heading_parts[1].strip()
                if any(c.isspace() for c in model):
                    # model name should not contain whitespaces - this heading is probably not really a role heading
                    continue
            else:
                model = None

            if last_section:
                last_section.content = self._grab_and_clean_up_lines(
                    md_lines, last_section.content_start_line, md_token.map[0]
                )
                sections.append(last_section)

            last_section = self._Section(
                role=role,
                model=model,
                content_start_line=md_token.map[1],
            )

        if last_section:
            last_section.content = self._grab_and_clean_up_lines(md_lines, last_section.content_start_line)
            sections.append(last_section)

        return tuple(Message(role=section.role, model=section.model, text=section.content) for section in sections)

    @staticmethod
    def _grab_and_clean_up_lines(md_lines: list[str], start_line: int, end_line: Optional[int] = None) -> str:
        """
        Grab a snippet of the markdown content by start and end line numbers and clean it up (remove leading
        and trailing empty lines).
        """
        if end_line is None:
            end_line = len(md_lines)

        content_lines = md_lines[start_line:end_line]

        # remove leading and trailing empty lines (but keep the leading and trailing whitespaces of the
        # non-empty lines)
        while content_lines and not content_lines[0].strip():
            content_lines.pop(0)
        while content_lines and not content_lines[-1].strip():
            content_lines.pop()

        if not content_lines:
            # there is no content in this section
            return ""

        return "\n".join(content_lines)

    @dataclass
    class _Section:
        """
        Represents a section of the markdown content.
        """

        role: str
        model: Optional[str]
        content_start_line: int
        content: Optional[str] = None
