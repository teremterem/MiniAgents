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

    heading: str
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

        if last_section:
            last_section.content = "\n".join(md_lines[last_section.content_start_line : md_token.map[0]])
            sections.append(last_section)

        last_section = Section(
            heading=md_tokens[idx + 1].content,  # the next token is `inline` with the heading content
            content_start_line=md_token.map[1],
        )

    if last_section:
        last_section.content = "\n".join(md_lines[last_section.content_start_line :])
        sections.append(last_section)

    messages = []
    for section in sections:
        heading_parts = section.heading.split("/", maxsplit=1)
        role = heading_parts[0].strip().lower()

        if role not in ["user", "assistant"]:
            continue

        if len(heading_parts) > 1:
            model = heading_parts[1].strip()
        else:
            model = None
        messages.append(Message(text=section.content, role=role, model=model))

    # TODO Oleksandr: cut off leading empty lines
    # TODO Oleksandr: cut off trailing whitespaces
    # TODO Oleksanr: skip empty sections
    return messages


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
