"""
A simple conversation example using the MiniAgents framework.
"""

import logging
from pathlib import Path

from dotenv import load_dotenv
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style

from miniagents.ext.llm.openai import create_openai_agent
from miniagents.ext.markdown.chat_history_md import ChatHistoryMD
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext
from miniagents.promising.sentinels import AWAIT
from miniagents.utils import achain_loop

load_dotenv()

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
    chat_history = ChatHistoryMD(CHAT_MD_FILE)

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

            chat_md_file.write(f"\n{utterance_title}\n========================================\n")
            print(f"\n{msg_promise.preliminary_metadata.agent_alias}: ", end="", flush=True)

            async for token in msg_promise:
                chat_md_file.write(token)
                print(token, end="", flush=True)

            chat_md_file.write("\n")
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
        chat_md_file.write(f"\nuser\n========================================\n{user_input}\n")

    chat_history = chat_history.load_chat_history()
    ctx.reply(chat_history)


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
