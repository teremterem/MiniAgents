"""
Parse a chat history in markdown format (work in progress).
TODO Oleksandr: this is a temporary example that will be deleted when the "history-in-md" utility is implemented.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from markdown_it import MarkdownIt

from miniagents.messages import Message

CHAT_MD_FILE = Path(__file__).parent / "../../../talk-about-miniagents/CHAT.md"

md = MarkdownIt()


@dataclass
class Section:
    """
    Represents a section of the markdown content.
    """

    role: str
    model: Optional[str]
    content_start_line: int
    content: Optional[str] = None


def parse_md_dialog(md_content: str) -> list[Message]:
    """
    Parse a markdown content as a dialog.
    """
    md_lines = md_content.split("\n")
    md_tokens = md.parse(md_content)

    last_section: Optional[Section] = None
    sections: list[Section] = []

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
            last_section.content = grab_and_clean_up_lines(md_lines, last_section.content_start_line, md_token.map[0])
            sections.append(last_section)

        last_section = Section(
            role=role,
            model=model,
            content_start_line=md_token.map[1],
        )

    if last_section:
        last_section.content = grab_and_clean_up_lines(md_lines, last_section.content_start_line)
        sections.append(last_section)

    # TODO Oleksandr: cut off leading empty lines
    # TODO Oleksandr: cut off trailing whitespaces
    # TODO Oleksanr: skip empty sections
    messages = [Message(role=section.role, model=section.model, text=section.content) for section in sections]
    return messages


def grab_and_clean_up_lines(md_lines: list[str], start_line: int, end_line: Optional[int] = None) -> str:
    """
    Grab a snippet of the markdown content by start and end line numbers and clean it up (remove leading and
    trailing empty lines).
    """
    if end_line is None:
        end_line = len(md_lines)

    content_lines = md_lines[start_line:end_line]

    # remove leading and trailing empty lines (but keep the leading and trailing whitespaces of the non-empty lines)
    while content_lines and not content_lines[0].strip():
        content_lines.pop(0)
    while content_lines and not content_lines[-1].strip():
        content_lines.pop()

    if not content_lines:
        # there is no content in this section
        return ""

    return "\n".join(content_lines)


def main() -> None:
    """
    Main function.
    """
    md_content = CHAT_MD_FILE.read_text(encoding="utf-8")

    for message in parse_md_dialog(md_content):
        print(repr(message.role))
        print(repr(message.text))
        print()


if __name__ == "__main__":
    main()
