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

from miniagents.ext.llm.llm_common import UserMessage
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
    chat_history = ChatHistoryMD(CHAT_MD_FILE, default_role="assistant")
    # technically `input_messages` are going to be the same as `ctx.messages`, but reading them instead of the
    # original `ctx.messages` ensures that all these messages will be logged to the chat history by the time
    # we are done iterating over `input_messages` here (because our async loop here will have to wait for the
    # `logging_agent` to finish in order to be sure that these are all the messages there are in `logging_agent`
    # response)
    input_messages = chat_history.logging_agent.inquire(ctx.messages)

    print("\033[92;1m", end="", flush=True)
    async for msg_promise in input_messages:
        print(f"\n{msg_promise.preliminary_metadata.agent_alias}: ", end="", flush=True)
        async for token in msg_promise:
            print(token, end="", flush=True)
        print("\n")

    # TODO Oleksandr: should MessageSequencePromise support `cancel()` operation
    #  (to interrupt whoever is producing it) ?

    # TODO Oleksandr: mention that ctrl+space is used to insert a newline ?
    user_input = await session.prompt_async(
        HTML("<user_utterance>USER: </user_utterance>"),
        multiline=True,
        key_bindings=bindings,
        lexer=CustomLexer(),
        style=style,
    )
    # the await below makes sure that writing to the chat history is finished before we proceed to reading it back
    await chat_history.logging_agent.inquire(UserMessage(user_input))

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
