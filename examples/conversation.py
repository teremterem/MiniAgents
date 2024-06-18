"""
A simple conversation example using the MiniAgents framework.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from markdown_it import MarkdownIt
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style

from miniagents.ext.llm.openai import create_openai_agent
from miniagents.messages import Message
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext
from miniagents.promising.sentinels import AWAIT
from miniagents.utils import achain_loop

load_dotenv()

md = MarkdownIt()

session = PromptSession()

bindings = KeyBindings()

CHAT_MD_FILE = Path(__file__).parent / "CHAT.md"


@bindings.add(Keys.Enter)
def _(event):
    event.current_buffer.validate_and_handle()


@bindings.add(Keys.ControlSpace)
def _(event):
    event.current_buffer.insert_text("\n")


class CustomLexer(Lexer):
    """
    Custom lexer that paints user utterances in yellow (and bold).
    """

    def lex_document(self, document: Document):
        """
        Lex the document.
        """
        return lambda i: [("class:user_utterance", document.text.split("\n")[i])]


style = Style.from_dict({"user_utterance": "fg:ansibrightyellow bold"})


@miniagent
async def user_agent(ctx: InteractionContext) -> None:
    """
    User agent that sends a message to the assistant and keeps track of the chat history.
    """
    with CHAT_MD_FILE.open("a", encoding="utf-8") as chat_md_file:
        print("\033[92;1m", end="", flush=True)
        async for msg_promise in ctx.messages:
            try:
                utterance_role = msg_promise.preliminary_metadata.role
            except AttributeError:
                utterance_role = "assistant"
            try:
                utterance_model = f" / {msg_promise.preliminary_metadata.model}"
            except AttributeError:
                utterance_model = ""
            utterance_title = f"{utterance_role}{utterance_model}"

            chat_md_file.write(f"{utterance_title}\n========================================\n")
            print(f"\n{msg_promise.preliminary_metadata.agent_alias}: ", end="", flush=True)

            async for token in msg_promise:
                chat_md_file.write(token)
                print(token, end="", flush=True)

            chat_md_file.write("\n\n")
            print("\n")

        chat_md_file.flush()

        # TODO Oleksandr: should MessageSequencePromise support `cancel()` operation
        #  (to interrupt whoever is producing it) ?

        user_input = await session.prompt_async(
            HTML("<user_utterance>USER: </user_utterance>"),
            multiline=True,
            key_bindings=bindings,
            lexer=CustomLexer(),
            style=style,
        )
        chat_md_file.write(f"user\n========================================\n{user_input}\n\n")

    chat_history = parse_md_dialog(CHAT_MD_FILE.read_text(encoding="utf-8"))
    ctx.reply(chat_history)


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
    TODO Oleksandr: implement exhaustive unit tests for this function
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

    return [Message(role=section.role, model=section.model, text=section.content) for section in sections]


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


async def amain() -> None:
    """
    The main conversation loop.
    """
    try:
        print()
        await achain_loop(
            [
                user_agent,
                AWAIT,
                create_openai_agent(model="gpt-4o-2024-05-13"),
            ]
        )
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    # logging.getLogger("miniagents.ext.llm").setLevel(logging.DEBUG)

    MiniAgents().run(amain())
