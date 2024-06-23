"""
This module provides a user agent that reads user input from the console, writes back to the console and also keeps
track of the chat history using the provided ChatHistory object.
"""

from pathlib import Path
from typing import Optional, Union

from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style

from miniagents.chat_history import ChatHistory, InMemoryChatHistory
from miniagents.ext.llm.llm_common import UserMessage
from miniagents.miniagents import miniagent, InteractionContext

GLOBAL_CHAT_HISTORY = InMemoryChatHistory()


@miniagent
async def console_user_agent(ctx: InteractionContext, chat_history: Optional[ChatHistory] = None) -> None:
    """
    User agent that reads user input from the console, writes back to the console and also keeps track of
    the chat history using the provided ChatHistory object.
    """
    if chat_history is None:
        chat_history = GLOBAL_CHAT_HISTORY

    # Let's wait for the `logging_agent` and `echo_agent` to finish before we proceed to the user input
    # TODO Oleksandr: should it be enough to just do `await msg_sequence_promise` instead of
    #  `await msg_sequence_promise.aresolve_messages()` to be sure that not only all message promises are "given"
    #  but all the messages are resolved ?
    # TODO Oleksandr: receive `echo_agent` as a parameter ?
    await echo_agent.inquire(chat_history.logging_agent.inquire(ctx.messages)).aresolve_messages()

    # TODO Oleksandr: should MessageSequencePromise support `cancel()` operation
    #  (to interrupt whoever is producing it) ?

    # TODO Oleksandr: mention that ctrl+space is used to insert a newline ?
    user_input = await _prompt_session.prompt_async(
        HTML("<user_utterance>USER: </user_utterance>"),
        multiline=True,
        key_bindings=_prompt_bindings,
        lexer=_CustomPromptLexer(),
        style=_user_prompt_style,
    )
    # the await below makes sure that writing to the chat history is finished before we proceed to reading it back
    await chat_history.logging_agent.inquire(UserMessage(user_input))

    chat_history = await chat_history.aload_chat_history()
    ctx.reply(chat_history)


@miniagent
async def echo_agent(
    ctx: InteractionContext, assistant_style: Union[str, int] = "92;1", mention_agents: bool = True
) -> None:
    """
    MiniAgent that echoes messages to the console token by token.
    """
    ctx.reply(ctx.messages)  # pass the same messages forward

    async for msg_promise in ctx.messages:
        if mention_agents:
            print(
                f"\n\033[{assistant_style}m{msg_promise.preliminary_metadata.agent_alias}: \033[0m", end="", flush=True
            )
        async for token in msg_promise:
            print(f"\033[{assistant_style}m{token}\033[0m", end="", flush=True)
        print("\n")  # this produces a double newline after a single message


@miniagent
async def file_agent(ctx: InteractionContext, file: str) -> None:
    """
    MiniAgent that writes the content of `messages` to a file.
    """
    ctx.reply(ctx.messages)  # pass the same messages forward

    file = Path(file)
    file.parent.mkdir(parents=True, exist_ok=True)

    with file.open("w", encoding="utf-8") as file_stream:
        async for token in ctx.messages.as_single_promise():
            file_stream.write(token)


_user_prompt_style = Style.from_dict({"user_utterance": "fg:ansibrightyellow bold"})

_prompt_session = PromptSession()

_prompt_bindings = KeyBindings()


@_prompt_bindings.add(Keys.Enter)
def _prompt_binding_enter(event):
    event.current_buffer.validate_and_handle()


@_prompt_bindings.add(Keys.ControlSpace)
def _prompt_binding_control_space(event):
    event.current_buffer.insert_text("\n")


class _CustomPromptLexer(Lexer):
    """
    Custom lexer that paints user utterances in yellow (and bold).
    """

    def lex_document(self, document: Document):
        """
        Lex the document.
        """
        return lambda i: [("class:user_utterance", document.text.split("\n")[i])]
