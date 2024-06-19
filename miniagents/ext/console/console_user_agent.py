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

from miniagents.ext.llm.llm_common import UserMessage
from miniagents.ext.markdown.chat_history_md import ChatHistoryMD
from miniagents.miniagents import miniagent, InteractionContext, MiniAgent


def create_console_user_agent(
    chat_history_md_file: Union[Path, str], alias: str = "USER_AGENT", **miniagent_kwargs
) -> MiniAgent:
    """
    Create a user agent that reads user input from the console, writes back to the console and also keeps
    track of the chat history using the provided ChatHistory object.
    """
    return miniagent(_console_user_agent, chat_history_md_file=chat_history_md_file, alias=alias, **miniagent_kwargs)


async def _console_user_agent(ctx: InteractionContext, chat_history_md_file: Union[Path, str]) -> None:
    """
    User agent that reads user input from the console, writes back to the console and also keeps track of
    the chat history using the provided ChatHistory object.
    """
    chat_history = ChatHistoryMD(chat_history_md_file, default_role="assistant")
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
    user_input = await _session.prompt_async(
        HTML("<user_utterance>USER: </user_utterance>"),
        multiline=True,
        key_bindings=_bindings,
        lexer=_CustomLexer(),
        style=_style,
    )
    # the await below makes sure that writing to the chat history is finished before we proceed to reading it back
    await chat_history.logging_agent.inquire(UserMessage(user_input))

    chat_history = chat_history.load_chat_history()
    ctx.reply(chat_history)


_style = Style.from_dict({"user_utterance": "fg:ansibrightyellow bold"})

_session = PromptSession()

_bindings = KeyBindings()


@_bindings.add(Keys.Enter)
def _binding_enter(event):
    event.current_buffer.validate_and_handle()


@_bindings.add(Keys.ControlSpace)
def _binding_control_space(event):
    event.current_buffer.insert_text("\n")


class _CustomLexer(Lexer):
    """
    Custom lexer that paints user utterances in yellow (and bold).
    """

    def lex_document(self, document: Document):
        """
        Lex the document.
        """
        return lambda i: [("class:user_utterance", document.text.split("\n")[i])]
