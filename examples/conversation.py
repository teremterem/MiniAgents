"""
A simple conversation example using the MiniAgents framework.
"""

from dotenv import load_dotenv
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style

from miniagents.ext.llm.openai import create_openai_agent
from miniagents.miniagent_typing import MessageType
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext
from miniagents.promising.sentinels import AWAIT
from miniagents.utils import achain_loop

load_dotenv()

session = PromptSession()

bindings = KeyBindings()

CHAT_HISTORY: list[MessageType] = []


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


style = Style.from_dict({"user_utterance": "fg:ansiyellow bold"})


@miniagent
async def user_agent(ctx: InteractionContext) -> None:
    """
    User agent that sends a message to the assistant and keeps track of the chat history.
    """
    print("\033[92;1m", end="", flush=True)
    async for msg_promise in ctx.messages:
        print(f"\n{msg_promise.preliminary_metadata.agent_alias}: ", end="", flush=True)
        async for token in msg_promise:
            print(token, end="", flush=True)
        print("\n")

    CHAT_HISTORY.append(ctx.messages)
    user_input = await session.prompt_async(
        HTML("<user_utterance>USER: </user_utterance>"),
        multiline=True,
        key_bindings=bindings,
        lexer=CustomLexer(),
        style=style,
    )
    CHAT_HISTORY.append(user_input)

    ctx.reply(CHAT_HISTORY)


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
    MiniAgents().run(amain())
