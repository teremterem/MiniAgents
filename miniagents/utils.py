# pylint: disable=import-outside-toplevel,cyclic-import
"""
Utility functions of the MiniAgents framework.
"""
import logging
import re
import traceback
import typing
from pathlib import Path
from typing import Any, AsyncIterator, Iterable, Optional, Union

# noinspection PyProtectedMember
from pydantic._internal._model_construction import ModelMetaclass

from miniagents.promising.sentinels import NO_VALUE

if typing.TYPE_CHECKING:
    from miniagents.messages import Message, MessagePromise, TextMessage
    from miniagents.miniagent_typing import MessageType
    from miniagents.miniagents import MiniAgent


class SingletonMeta(type):
    """
    A metaclass that ensures that only one instance of a certain class is created.
    NOTE: This metaclass is designed to work in asynchronous environments, hence we didn't bother making
    it thread-safe (people typically don't mix multithreading and asynchronous paradigms together).
    """

    # TODO make it thread-safe just in case ? (for the sake of tricks like `asyncio.to_thread()` and similar)

    def __call__(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__call__()
        return cls._instance


class Singleton(metaclass=SingletonMeta):
    """
    A class that ensures that only one instance of a certain class is created.
    """


class ModelSingletonMeta(ModelMetaclass, SingletonMeta):
    """
    A metaclass that ensures that only one instance of a Pydantic model of a certain class is created.
    """


class ModelSingleton(metaclass=ModelSingletonMeta):
    """
    A class that ensures that only one instance of a Pydantic model of a certain class is created.
    """


def as_single_text_promise(
    messages: "MessageType",
    *,
    delimiter: Optional[str] = "\n\n",
    strip_leading_newlines: bool = False,
    reference_original_messages: bool = True,
    start_soon: Optional[bool] = False,
    message_class: Optional[type["TextMessage"]] = None,
    **known_beforehand,
) -> "MessagePromise":
    """
    Join multiple messages into a single text message using a delimiter.

    :param messages: Messages to join.
    :param delimiter: A string that will be inserted between messages.
    :param strip_leading_newlines: If True, leading newlines will be stripped from each message. Language models,
    when prompted in a certain way, may produce leading newlines in the response. This parameter allows you to
    remove them.
    :param reference_original_messages: If True, the resulting message will contain the list of original messages
    in the `original_messages` field.
    :param start_soon: If True, the resulting message will be scheduled for background resolution regardless
    of when it is going to be consumed.
    :param known_beforehand: Message fields that will be available under `MessagePromise.known_beforehand` even
    before the promise is resolved.
    :param message_class: A class of the resulting message. If None, the default TextMessage class will be used.
    """
    from miniagents.messages import MessageSequence, TextMessage, Token, TextToken

    if start_soon is None:
        start_soon = NO_VALUE  # inherit the default value from the current MiniAgents context

    if message_class is None:
        message_class = TextMessage

    async def token_streamer(fields_so_far: dict[str, Any]) -> AsyncIterator[Token]:
        if reference_original_messages:
            fields_so_far["original_messages"] = []

        first_message = True
        async for message_promise in MessageSequence.turn_into_sequence_promise(messages):
            fields_so_far.update(
                (key, value)
                for key, value in message_promise.known_beforehand
                if key not in message_promise.message_class.non_metadata_fields()
            )
            if delimiter and not first_message:
                yield delimiter

            lstrip_newlines = strip_leading_newlines
            async for token in message_promise:
                if lstrip_newlines and isinstance(token, TextToken):
                    # let's remove leading newlines from the first message
                    original_token_str = str(token)
                    token_str = original_token_str.lstrip("\n\r")
                    if original_token_str != token_str:
                        token = token.model_copy(update={"content": token_str})
                if str(token):
                    lstrip_newlines = False  # non-empty token was found - time to stop stripping newlines
                yield token

            if reference_original_messages:
                fields_so_far["original_messages"].append(await message_promise)

            # TODO should we care about merging values of the same keys instead of just overwriting them ?
            #  (if not, add a comment about this)
            fields_so_far.update(
                (key, value)
                for key, value in await message_promise
                if key not in message_promise.message_class.non_metadata_fields()
            )

            first_message = False

    return message_class.promise(
        message_token_streamer=token_streamer,
        start_soon=start_soon,
        **known_beforehand,
    )


class MiniAgentsLogFormatter(logging.Formatter):
    """
    A custom log formatter that hides traceback lines that reference scripts which reside in `packages_to_exclude` and
    shows the agent trace if `include_agent_trace` is True.
    """

    packages_to_exclude: list[Path]
    include_agent_trace: bool

    def __init__(
        self, *args, packages_to_exclude: Optional[Iterable[Path]] = None, include_agent_trace: bool = True, **kwargs
    ):
        super().__init__(*args, **kwargs)
        if packages_to_exclude is None:
            packages_to_exclude = [Path(__file__).parent]  # the whole "miniagents" library by default
        self.packages_to_exclude = packages_to_exclude
        self.include_agent_trace = include_agent_trace

    @staticmethod
    def _get_script_path(line: str) -> Optional[Path]:
        match: re.Match = re.search(r'^\s*File "(.+?\.py)", line \d+, in ', line)
        if not match:
            return None

        return Path(match.group(1))

    def formatException(self, ei) -> str:
        from miniagents.miniagents import MiniAgents
        from miniagents.promising.errors import PromisingContextError

        try:
            log_reduced_tracebacks = MiniAgents.get_current().log_reduced_tracebacks
        except PromisingContextError:
            log_reduced_tracebacks = False

        lines = traceback.format_exception(*ei)

        if log_reduced_tracebacks:
            # first we will collect script paths in `show_line`, but later we will replace them with true/false flags
            # to indicate whether the corresponding traceback lines should be shown or not
            show_line: list[Union[Optional[Path], bool]] = [self._get_script_path(line) for line in lines]

            exception_origin_already_shown = False
            for line_no in range(len(show_line) - 1, -1, -1):
                script_path = show_line[line_no]
                if not script_path:
                    # this line does not represent any particular script - we show it
                    show_line[line_no] = True
                    continue

                if not any(script_path.is_relative_to(pkg) for pkg in self.packages_to_exclude):
                    # it's a script, but not from `packages_to_exclude` - we show it
                    show_line[line_no] = True
                    exception_origin_already_shown = True
                    continue

                if not exception_origin_already_shown:
                    # it's a script from `packages_to_exclude`, but it's the very last script in the traceback -
                    # we show it, because it discloses the origin of the exception
                    show_line[line_no] = True
                    exception_origin_already_shown = True
                    continue

                # it's a script from `packages_to_exclude` and it's not the very last one in the traceback - we hide it
                # to reduce the verbosity of the traceback
                show_line[line_no] = False

            lines = [line for line, show in zip(lines, show_line) if show]
            lines.append(
                "\n"
                "ATTENTION! Some parts of the traceback above are omitted for readability.\n"
                "Use `MiniAgents(log_reduced_tracebacks=False)` to see the full traceback.\n"
            )

        # Add the agent trace if enabled
        if self.include_agent_trace:
            try:
                lines.append(f"\nAgent trace:\n{display_agent_trace()}\n---\n")
            except PromisingContextError:
                pass

        return "".join(lines)


def get_current_agent_trace() -> list["MiniAgent"]:
    """
    Get the current agent trace.
    """
    from miniagents.miniagents import InteractionContext

    return InteractionContext.get_current().get_agent_trace()


def display_agent_trace(agent_trace: Optional[Iterable["MiniAgent"]] = None) -> str:
    """
    Display the current agent trace, or the one provided as an argument.
    """
    if agent_trace is None:
        agent_trace = get_current_agent_trace()
    return " <- ".join([agent.alias for agent in agent_trace])


def dict_to_message(d: dict[str, Any]) -> "Message":
    from miniagents.messages import TextMessage, Message

    if any(isinstance(d.get(field), str) for field in TextMessage.non_metadata_fields()):
        return TextMessage(**d)
    return Message(**d)
