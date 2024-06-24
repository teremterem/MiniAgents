"""
This module provides a user agent that reads user input from the console, writes back to the console and also keeps
track of the chat history using the provided ChatHistory object.
"""

from pathlib import Path
from typing import Union

from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style

from miniagents.chat_history import InMemoryChatHistory
from miniagents.ext.llm.llm_common import UserMessage
from miniagents.miniagents import miniagent, InteractionContext

GLOBAL_CHAT_HISTORY = InMemoryChatHistory()


@miniagent
async def prompt_agent(ctx: InteractionContext) -> None:
    """
    TODO Oleksandr: docstring
    """
    # this is a "transparent" agent - pass the same messages forward (if any)
    ctx.reply(ctx.messages)
    # let's wait for all the previous messages to be resolved before we show the user prompt
    # TODO Oleksandr: just use `await ctx.messages` here (fix MessageSequencePromise to work this way)
    await ctx.messages.aresolve_messages()

    # TODO Oleksandr: find a way to mention that ctrl+space is used to insert a newline ?
    user_input = await _prompt_session.prompt_async(
        HTML("<user_utterance>USER: </user_utterance>"),
        multiline=True,
        key_bindings=_prompt_bindings,
        lexer=_CustomPromptLexer(),
        style=_user_prompt_style,
    )
    print()  # skip an extra line after the user input

    ctx.reply(UserMessage(user_input))


@miniagent
async def echo_agent(
    ctx: InteractionContext, assistant_style: Union[str, int] = "92;1", mention_aliases: bool = True
) -> None:
    """
    MiniAgent that echoes messages to the console token by token.
    """
    ctx.reply(ctx.messages)  # this is a "transparent" agent - pass the same messages forward

    # TODO Oleksandr: should MessageSequencePromise support `cancel()` operation
    #  (to interrupt whoever is producing it) ?

    async for msg_promise in ctx.messages:
        if mention_aliases:
            print(
                f"\033[{assistant_style}m{msg_promise.preliminary_metadata.agent_alias}: \033[0m", end="", flush=True
            )
        async for token in msg_promise:
            print(f"\033[{assistant_style}m{token}\033[0m", end="", flush=True)
        print("\n")  # this produces a double newline after a single message


@miniagent
async def file_agent(ctx: InteractionContext, file: Union[str, Path]) -> None:
    """
    MiniAgent that writes the content of `messages` to a file.
    """
    ctx.reply(ctx.messages)  # this is a "transparent" agent - pass the same messages forward

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
