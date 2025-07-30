# pylint: disable=import-outside-toplevel,cyclic-import
"""
Utility functions of the MiniAgents framework.
"""
import logging
import re
import threading
import traceback
import typing
from pathlib import Path
from typing import Any, AsyncIterator, Iterable, Optional, Union

# noinspection PyProtectedMember
from pydantic._internal._model_construction import ModelMetaclass

from miniagents.promising.sentinels import NO_VALUE

if typing.TYPE_CHECKING:
    from miniagents.messages import MessagePromise, TextMessage
    from miniagents.miniagent_typing import MessageType
    from miniagents.miniagents import MiniAgent


class SingletonMeta(type):
    """
    A metaclass that ensures that only one instance of a certain class is created.

    Even though MiniAgents framework is async, this metaclass is still thread-safe, to widen the scope of use cases.

    Parameters for singleton instantiation:
    - singleton_scope: The scope object where the singleton instance will be stored.
                       If None, the class itself is used as the scope (global singleton).
    - singleton_scope_key: The attribute/key name for storing the instance in the scope.
                           If None, defaults to "__instance" for class scope or "__{ClassName}_instance" for custom
                           scopes.
    - singleton_scope_as_dict: If True, treat the scope as a dictionary when storing the instance.
                               If False, treat it as an object and store the instance as an attribute.

    NOTE: To avoid complaints from some IDEs about unexpected keyword arguments from the singleton parameters, classes
    using this metaclass could accept `**_` in their `__init__`.
    """

    def __new__(mcs, name, bases, dct):
        singleton_cls = super().__new__(mcs, name, bases, dct)
        singleton_cls.__singleton_lock = threading.Lock()  # pylint: disable=protected-access,unused-private-member
        return singleton_cls

    def __call__(
        cls,
        *,
        singleton_scope: Any = None,
        singleton_scope_key: Optional[str] = None,
        singleton_scope_as_dict: bool = False,
    ):
        if singleton_scope_key is None:
            if singleton_scope is None:
                # The scope of the singleton is the class itself => no need to duplicate the class name in the key
                singleton_scope_key = "__instance"
            else:
                singleton_scope_key = f"__{cls.__name__}_instance"

        if singleton_scope is None:
            # The scope of the singleton is the class itself (global singleton)
            singleton_scope = cls

        if singleton_scope_as_dict:
            # The scope is a dictionary => use [] notation
            if singleton_scope_key not in singleton_scope:
                with cls.__singleton_lock:
                    # Double check in case of race condition
                    if singleton_scope_key not in singleton_scope:
                        singleton_scope[singleton_scope_key] = super().__call__()

            return singleton_scope[singleton_scope_key]

        # The scope is NOT a dictionary => use hasattr/setattr/getattr()
        if not hasattr(singleton_scope, singleton_scope_key):
            with cls.__singleton_lock:
                # Double check in case of race condition
                if not hasattr(singleton_scope, singleton_scope_key):
                    setattr(singleton_scope, singleton_scope_key, super().__call__())

        return getattr(singleton_scope, singleton_scope_key)


class Singleton(metaclass=SingletonMeta):
    """
    A base class for singletons.

    Parameters for singleton instantiation (see `SingletonMeta` for more details):
    - singleton_scope: The scope object where the singleton instance will be stored.
                       If None, the class itself is used as the scope (global singleton).
    - singleton_scope_key: The attribute/key name for storing the instance in the scope.
                           If None, defaults to "__instance" for class scope or "__{ClassName}_instance" for custom
                           scopes.
    - singleton_scope_as_dict: If True, treat the scope as a dictionary when storing the instance.
                               If False, treat it as an object and store the instance as an attribute.

    NOTE: To avoid complaints from some IDEs about unexpected keyword arguments from the singleton parameters, classes
    inheriting from this one could accept `**_` in their `__init__`.
    """


class ModelSingletonMeta(ModelMetaclass, SingletonMeta):
    """
    A metaclass that ensures that only one instance of a Pydantic model of a certain class is created.
    """


class ModelSingleton(metaclass=ModelSingletonMeta):
    """
    A base class that ensures that only one instance of a Pydantic model of a certain class is created.

    This base class exists separately from `Singleton` because Pydantic models cannot be extended from `Singleton`.
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

    async def token_streamer(auxiliary_field_collector: dict[str, Any]) -> AsyncIterator[Token]:
        if reference_original_messages:
            auxiliary_field_collector["original_messages"] = []

        first_message = True
        async for message_promise in MessageSequence.turn_into_sequence_promise(messages):
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
                auxiliary_field_collector["original_messages"].append(await message_promise)

            # TODO should we care about merging values of the same keys instead of just overwriting them ?
            #  (if not, add a comment about this)
            auxiliary_field_collector.update(
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
        else:
            lines.append(
                "\n"
                "ATTENTION! All the traceback lines are shown (including those from `miniagents` library).\n"
                "Use `MiniAgents(log_reduced_tracebacks=True)` to only show the lines from the scripts you wrote.\n"
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
