"""
This module provides a user agent that reads user input from the console, writes back to the console and also keeps
track of the chat history using the provided ChatHistory object.
"""

from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style

from miniagents.chat_history import ChatHistory, InMemoryChatHistory
from miniagents.ext.llm.llm_common import UserMessage
from miniagents.miniagents import miniagent, InteractionContext, MiniAgent


def create_console_user_agent(
    chat_history: ChatHistory = None, alias: str = "USER_AGENT", **miniagent_kwargs
) -> MiniAgent:
    """
    Create a user agent that reads user input from the console, writes back to the console and also keeps
    track of the chat history using the provided ChatHistory object.
    """
    if chat_history is None:
        chat_history = InMemoryChatHistory()
    return miniagent(_console_user_agent, chat_history=chat_history, alias=alias, **miniagent_kwargs)


async def _console_user_agent(ctx: InteractionContext, chat_history: ChatHistory) -> None:
    """
    User agent that reads user input from the console, writes back to the console and also keeps track of
    the chat history using the provided ChatHistory object.
    """
    # technically `input_messages` are going to be the same as `ctx.messages`, but reading them instead of the
    # original `ctx.messages` ensures that all these messages will be logged to the chat history by the time
    # we are done iterating over `input_messages` here (because our async loop here will have to wait for the
    # `logging_agent` to finish in order to be sure that these are all the messages there are in `logging_agent`
    # response)
    input_messages = chat_history.logging_agent.inquire(ctx.messages)

    assistant_style = "\033[92;1m"
    cancel_style = "\033[0m"

    async for msg_promise in input_messages:
        print(f"\n{assistant_style}{msg_promise.preliminary_metadata.agent_alias}: {cancel_style}", end="", flush=True)
        async for token in msg_promise:
            print(f"{assistant_style}{token}{cancel_style}", end="", flush=True)
        print("\n")

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
