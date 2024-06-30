"""
This module provides agents working with chat history.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from markdown_it import MarkdownIt

from miniagents.messages import Message
from miniagents.miniagents import InteractionContext, miniagent


@miniagent
async def in_memory_history_agent(ctx: InteractionContext, message_list: list[Message]) -> None:
    """
    TODO Oleksandr: docstring
    """
    message_list.extend(await ctx.message_promises)
    ctx.reply(message_list)


@miniagent
async def markdown_history_agent(
    ctx: InteractionContext,
    history_md_file: Union[str, Path] = "CHAT.md",
    default_role: str = "assistant",
    only_write: bool = False,
    append: bool = True,
) -> None:
    """
    An agent that logs the `messages` to a markdown file and then returns all the messages in the chat history
    file as a reply (including the ones that existed in the file before the current interaction).
    """
    history_md_file = Path(history_md_file)
    history_md_file.parent.mkdir(parents=True, exist_ok=True)

    # log the current messages to the chat history file
    with history_md_file.open(
        mode="a" if append else "w",
        buffering=1,  # line buffering
        encoding="utf-8",
    ) as chat_md_file:
        async for msg_promise in ctx.message_promises:
            if getattr(msg_promise.preliminary_metadata, "no_history", False):
                # do not log this message to the chat history
                continue

            try:
                message_role = msg_promise.preliminary_metadata.role
            except AttributeError:
                message_role = default_role
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

    if not only_write:
        # return the full chat history (including the messages that were already in the file before) as a reply
        ctx.reply(_load_chat_history_md(history_md_file))


_md = MarkdownIt()


def _load_chat_history_md(history_md_file: Path) -> tuple[Message, ...]:
    """
    Parse a markdown content as a dialog.
    TODO Oleksandr: implement exhaustive unit tests for this function
    """
    md_content = history_md_file.read_text(encoding="utf-8")

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
            last_section.content = _grab_and_clean_up_lines(md_lines, last_section.content_start_line, md_token.map[0])
            sections.append(last_section)

        last_section = _Section(role=role, model=model, content_start_line=md_token.map[1])

    if last_section:
        last_section.content = _grab_and_clean_up_lines(md_lines, last_section.content_start_line)
        sections.append(last_section)

    return tuple(Message(role=section.role, model=section.model, text=section.content) for section in sections)


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
