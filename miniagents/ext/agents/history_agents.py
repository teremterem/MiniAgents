"""
This module provides agents working with chat history.
"""

import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from pprint import pformat
from typing import Optional

from markdown_it import MarkdownIt
from pydantic import BaseModel, ConfigDict

from miniagents.messages import MESSAGE_CONTENT_FIELD, Message
from miniagents.miniagents import InteractionContext, miniagent
from miniagents.promising.ext.frozen import Frozen

GLOBAL_MESSAGE_HISTORY: list[Message] = []


@miniagent(mutable_state={"message_list": GLOBAL_MESSAGE_HISTORY})
async def in_memory_history_agent(
    ctx: InteractionContext, message_list: list[Message], return_full_history: bool = False
) -> None:
    """
    An agent that stores incoming messages in the `message_list` and then returns all the messages that this list
    already contains as a reply (including the ones that existed in the list before the current interaction).
    """
    if not return_full_history:
        # just pass the incoming messages through
        ctx.reply(ctx.message_promises)

    message_list.extend(await ctx.message_promises)

    if return_full_history:
        ctx.reply(message_list)


@miniagent
class MarkdownHistoryAgent(BaseModel):
    """
    An agent that logs the `messages` to a markdown file and then returns all the messages in the chat history
    file as a reply (including the ones that existed in the file before the current interaction).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    ctx: InteractionContext
    history_md_file: str = "CHAT.md"
    default_role: str = "assistant"
    return_full_history: bool = False
    append: bool = True
    skip_empty: bool = True
    ignore_no_history: bool = False

    async def __call__(self) -> None:
        if not self.return_full_history:
            # just pass the incoming messages through
            self.ctx.reply(self.ctx.message_promises)

        history_md_file = Path(self.history_md_file)
        history_md_file.parent.mkdir(parents=True, exist_ok=True)

        # log the current messages to the chat history file
        with history_md_file.open(
            mode="a" if self.append else "w",
            buffering=1,  # line buffering
            encoding="utf-8",
        ) as chat_md_file:
            async for msg_promise in self.ctx.message_promises:
                if getattr(msg_promise.preliminary_metadata, "no_history", False) and not self.ignore_no_history:
                    # do not log this message to the chat history
                    continue

                try:
                    message_role = msg_promise.preliminary_metadata.role
                except AttributeError:
                    message_role = self.default_role
                try:
                    message_model = msg_promise.preliminary_metadata.model or ""
                except AttributeError:
                    message_model = ""

                if message_model:
                    message_model = f" / {message_model}"

                chat_md_file.write(f"\n{message_role}{message_model}\n========================================\n")

                async for token in msg_promise:
                    chat_md_file.write(token)
                chat_md_file.write("\n")

        if self.return_full_history:
            # return the full chat history (including the messages that were already in the file before) as a reply
            chat_history = self._load_chat_history_md()
            if self.skip_empty:
                chat_history = tuple(msg for msg in chat_history if msg.content and msg.content.strip())
            self.ctx.reply(chat_history)

    def _load_chat_history_md(self) -> tuple[Message, ...]:
        """
        Parse a markdown content as a dialog.
        TODO Oleksandr: implement exhaustive unit tests for this function ?
        """
        md_content = Path(self.history_md_file).read_text(encoding="utf-8")

        md_lines = md_content.split("\n")
        md_tokens = _md.parse(md_content)

        last_section = None
        sections = []

        for idx, md_token in enumerate(md_tokens):
            if md_token.type != "heading_open" or md_token.tag != "h1" or md_token.level != 0:
                continue

            heading = md_tokens[idx + 1].content  # the next token is `inline` with the heading content
            heading_parts = heading.split("/", maxsplit=1)
            role = heading_parts[0].strip().lower()

            if role not in ["system", "user", "assistant"]:
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

            last_section = self._Section(role=role, model=model, content_start_line=md_token.map[1])

        if last_section:
            last_section.content = self._grab_and_clean_up_lines(md_lines, last_section.content_start_line)
            sections.append(last_section)

        return tuple(Message(role=section.role, model=section.model, content=section.content) for section in sections)

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


@miniagent
async def markdown_llm_logger_agent(
    ctx: InteractionContext,
    log_folder: str = "llm_logs/",
    request_metadata: Optional[Frozen] = None,
    show_response_metadata: bool = True,
) -> None:
    """
    TODO Oleksandr: docstring
    """
    log_folder = Path(log_folder)
    log_folder.mkdir(parents=True, exist_ok=True)

    try:
        model_suffix = f"__{request_metadata.model}"
    except AttributeError:
        model_suffix = ""

    log_file = log_folder / (
        f"{datetime.now().strftime('%Y%m%d_%H%M%S__%f')}{model_suffix}__{random.randint(0, 0xfff):03x}.md"
    )

    if log_file.exists():
        # this should not happen - not only there are milliseconds in the file name, but also a random number in the
        # range of 0 through 4095 (0 through 0xfff)
        raise FileExistsError(f"Log file already exists: {log_file}")

    if request_metadata:
        log_file.write_text(f"```python\n{pformat(request_metadata.model_dump())}\n```\n", encoding="utf-8")

    await MarkdownHistoryAgent.inquire(ctx.message_promises, history_md_file=str(log_file), ignore_no_history=True)

    messages = await ctx.message_promises
    if not messages or not show_response_metadata:
        return

    response_metadata = messages[-1].model_dump(exclude={MESSAGE_CONTENT_FIELD})
    with log_file.open(mode="a", buffering=1, encoding="utf-8") as log_file:
        log_file.write(f"\n----------------------------------------\n\n```python\n{pformat(response_metadata)}\n```\n")


_md = MarkdownIt()
