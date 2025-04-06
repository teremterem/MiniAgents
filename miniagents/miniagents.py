"""
"Core" classes of the MiniAgents framework.
"""

import asyncio
import contextvars
import logging
import re
import warnings
from contextvars import ContextVar
from typing import Any, AsyncIterator, Awaitable, Callable, Iterable, Optional, Union

from pydantic import Field

from miniagents.messages import (
    Message,
    MessagePromise,
    MessageSequence,
    MessageSequenceAppender,
    MessageSequencePromise,
)
from miniagents.miniagent_typing import AgentFunction, MessageType, PersistMessageEventHandler
from miniagents.promising.errors import NoActiveContextError, WrongActiveContextError
from miniagents.promising.ext.frozen import Frozen
from miniagents.promising.promise_typing import PromiseResolvedEventHandler
from miniagents.promising.promising import Promise, PromisingContext
from miniagents.utils import MiniAgentsLogFormatter


_default_logger = logging.Logger("MiniAgents", level=logging.WARNING)
_log_formatter = MiniAgentsLogFormatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
_log_handler = logging.StreamHandler()
_log_handler.setFormatter(_log_formatter)
_default_logger.addHandler(_log_handler)


class MiniAgents(PromisingContext):
    stream_llm_tokens_by_default: bool
    llm_logger_agent: Union["MiniAgent", bool]
    normalize_agent_func_and_class_names: bool
    normalize_spaces_in_agent_docstrings: bool
    on_persist_message_handlers: list[PersistMessageEventHandler]
    log_reduced_tracebacks: bool

    logger: logging.Logger = _default_logger

    def __init__(
        self,
        *,
        stream_llm_tokens_by_default: bool = True,
        llm_logger_agent: Union["MiniAgent", bool] = False,
        normalize_agent_func_and_class_names: bool = True,
        normalize_spaces_in_agent_docstrings: bool = True,
        on_persist_message: Union[PersistMessageEventHandler, Iterable[PersistMessageEventHandler]] = (),
        on_promise_resolved: Union[PromiseResolvedEventHandler, Iterable[PromiseResolvedEventHandler]] = (),
        log_reduced_tracebacks: bool = True,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ) -> None:
        on_promise_resolved = (
            [self._trigger_persist_message_event, on_promise_resolved]
            if callable(on_promise_resolved)
            else [self._trigger_persist_message_event, *on_promise_resolved]
        )
        super().__init__(on_promise_resolved=on_promise_resolved, logger=logger, **kwargs)

        self.log_reduced_tracebacks = log_reduced_tracebacks
        self.stream_llm_tokens_by_default = stream_llm_tokens_by_default
        self.llm_logger_agent = llm_logger_agent
        self.normalize_agent_func_and_class_names = normalize_agent_func_and_class_names
        self.normalize_spaces_in_agent_docstrings = normalize_spaces_in_agent_docstrings
        self.on_persist_message_handlers: list[PersistMessageEventHandler] = (
            [on_persist_message] if callable(on_persist_message) else list(on_persist_message)
        )

        self._child_agent_calls: set[AgentCall] = set()

    @classmethod
    def get_current(cls) -> "MiniAgents":
        current = super().get_current()
        if not isinstance(current, MiniAgents):
            raise WrongActiveContextError(
                f"The active context was expected to be of type {cls.__name__}, "
                f"but it is of type {type(current).__name__} instead."
            )
        return current

    def on_persist_message(self, handler: PersistMessageEventHandler) -> PersistMessageEventHandler:
        """
        Add a handler that will be called every time a Message needs to be persisted.
        """
        self.on_persist_message_handlers.append(handler)
        return handler

    async def afinalize(self) -> None:
        for agent_call in list(self._child_agent_calls):
            agent_call.finish()
        await super().afinalize()

    # noinspection PyProtectedMember
    async def _trigger_persist_message_event(self, _, obj: Any) -> None:
        # pylint: disable=protected-access
        if not isinstance(obj, Message):
            return

        for sub_message in obj.sub_messages():
            if sub_message._persist_message_event_triggered:
                continue

            for handler in self.on_persist_message_handlers:
                self.start_soon(handler(_, sub_message))
            sub_message._persist_message_event_triggered = True

        if obj._persist_message_event_triggered:
            return

        for handler in self.on_persist_message_handlers:
            self.start_soon(handler(_, obj))
        obj._persist_message_event_triggered = True


def miniagent(
    func_or_class: Optional[Union[AgentFunction, type]] = None,
    *,
    alias: Optional[str] = None,
    description: Optional[str] = None,
    normalize_func_or_class_name: bool = True,
    normalize_spaces_in_docstring: bool = True,
    interaction_metadata: Optional[dict[str, Any]] = None,
    mutable_state: Optional[dict[str, Any]] = None,
    **kwargs_to_freeze,
) -> Union["MiniAgent", Callable[[AgentFunction], "MiniAgent"]]:
    """
    A decorator that converts an agent function into an agent.
    """
    if func_or_class is None:
        # the decorator `@miniagent(...)` was used with arguments
        def _decorator(f_or_cls: Union[AgentFunction, type]) -> "MiniAgent":
            return MiniAgent(
                f_or_cls,
                alias=alias,
                description=description,
                normalize_func_or_class_name=normalize_func_or_class_name,
                normalize_spaces_in_docstring=normalize_spaces_in_docstring,
                interaction_metadata=interaction_metadata,
                mutable_state=mutable_state,
                **kwargs_to_freeze,
            )

        return _decorator

    # the decorator `@miniagent` was used either without arguments or as a direct function call
    return MiniAgent(
        func_or_class,
        alias=alias,
        description=description,
        normalize_func_or_class_name=normalize_func_or_class_name,
        normalize_spaces_in_docstring=normalize_spaces_in_docstring,
        interaction_metadata=interaction_metadata,
        mutable_state=mutable_state,
        **kwargs_to_freeze,
    )


class MiniAgent(Frozen):
    """
    A wrapper for an agent function that allows calling the agent.
    """

    alias: str
    description: Optional[str] = Field(exclude=True)
    interaction_metadata: Frozen = Field(exclude=True)

    def __init__(
        self,
        func_or_class: Union[AgentFunction, type],
        *,
        alias: Optional[str] = None,
        description: Optional[str] = None,
        normalize_func_or_class_name: Optional[bool] = None,
        normalize_spaces_in_docstring: Optional[bool] = None,
        interaction_metadata: Optional[Union[dict[str, Any], Frozen]] = None,
        mutable_state: Optional[dict[str, Any]] = None,
        **kwargs_to_freeze,
    ) -> None:
        if normalize_func_or_class_name is None:
            normalize_func_or_class_name = MiniAgents.get_current().normalize_agent_func_and_class_names
        if normalize_spaces_in_docstring is None:
            normalize_spaces_in_docstring = MiniAgents.get_current().normalize_spaces_in_agent_docstrings

        if alias is None:
            alias = func_or_class.__name__
            if normalize_func_or_class_name:
                # split `alias` by capitalization, assuming it is in camel case
                # (if it is not, it will not be split)
                alias = "_".join(part for part in re.findall(r"[A-Z][a-z]+?(?=[A-Z]+$)|.+?(?=[A-Z][a-z]|$)", alias))
                alias = alias.upper()

        if description is None:
            description = func_or_class.__doc__
            if description and normalize_spaces_in_docstring:
                description = " ".join(description.split())
        if description:
            # replace all {AGENT_ALIAS} entries in the description with the actual agent alias
            description = description.format(AGENT_ALIAS=alias)

        # validate interaction metadata
        # TODO is `interaction_metadata` a good name ? see how it is used in Recensia to decide
        interaction_metadata = Frozen(**dict(interaction_metadata or {}))

        super().__init__(alias=alias, description=description, interaction_metadata=interaction_metadata)
        self.__name__ = alias
        self.__doc__ = description

        self._func_or_class = func_or_class
        self._static_kwargs = Frozen(**kwargs_to_freeze).as_kwargs()
        self._mutable_state = dict(mutable_state or {})

    def trigger(
        self,
        messages: Optional[MessageType] = None,
        start_soon: Optional[bool] = None,
        errors_to_messages: bool = False,
        **kwargs_to_freeze,
    ) -> MessageSequencePromise:
        agent_call = self.initiate_call(
            start_soon=start_soon, errors_to_messages=errors_to_messages, **kwargs_to_freeze
        )
        if messages is not None:
            agent_call.send_message(messages)
        return agent_call.reply_sequence()

    # noinspection PyProtectedMember
    def initiate_call(
        self, start_soon: Optional[bool] = None, errors_to_messages: bool = False, **kwargs_to_freeze
    ) -> "AgentCall":
        """
        Start a call with the agent. The agent will be called with the provided function kwargs.
        TODO expand this docstring ?
        """
        input_sequence = MessageSequence(
            start_soon=False,
        )
        reply_sequence = AgentReplyMessageSequence(
            mini_agent=self,
            kwargs_to_freeze=kwargs_to_freeze,
            input_sequence_promise=input_sequence.sequence_promise,
            start_soon=start_soon,
            errors_to_messages=errors_to_messages,
        )

        agent_call = AgentCall(
            message_streamer=input_sequence.message_appender,
            reply_sequence_promise=reply_sequence.sequence_promise,
        )
        return agent_call

    def fork(
        self,
        alias: Optional[str] = None,  # TODO enforce unique aliases ? introduce a "fork identifier" ?
        description: Optional[str] = None,
        *,
        interaction_metadata: Optional[Union[dict[str, Any], Frozen]] = None,
        mutable_state: Optional[dict[str, Any]] = None,
        **kwargs_to_freeze,
    ) -> Union["MiniAgent", Callable[[AgentFunction], "MiniAgent"]]:
        """
        Create a forked version of this agent with modified parameters.

        Args:
            alias: New alias for the forked agent. If not provided, uses the original alias.
            description: New description for the forked agent. If not provided, uses the original description.
            interaction_metadata: TODO explain this parameter
            mutable_state: Additional mutable state to merge with the original mutable state.
            **kwargs_to_freeze: Additional static parameters for the forked agent.

        Returns:
            A new MiniAgent instance with the modified parameters.
        """
        return MiniAgent(
            self._func_or_class,
            alias=alias or self.alias,
            description=description or self.description,
            normalize_func_or_class_name=False,
            normalize_spaces_in_docstring=False,
            interaction_metadata={**dict(self.interaction_metadata), **dict(interaction_metadata or {})},
            mutable_state={**self._mutable_state, **(mutable_state or {})},
            **self._static_kwargs,
            **kwargs_to_freeze,
        )

    def original_def(self) -> Union[AgentFunction, type]:
        """
        Get the original definition of the agent, which is either a function or a class. The `@miniagent` decorator
        hides the original function or class from the client code behind a `MiniAgent` object, but in certain scenarios
        access to the original function or class might be needed. This method provides exactly that.
        """
        # TODO do it the other way around ? return the original definition from the decorator and just
        # attach the key methods (trigger, initiate_call, fork etc.) as well as an instance of `MiniAgent` to it ?
        return self._func_or_class


class InteractionContext:
    this_agent: MiniAgent
    message_promises: MessageSequencePromise

    _current: ContextVar[Optional["InteractionContext"]] = ContextVar("InteractionContext._current", default=None)

    def __init__(
        self,
        this_agent: "MiniAgent",
        message_promises: MessageSequencePromise,
        reply_streamer: MessageSequenceAppender,
    ) -> None:
        self.this_agent = this_agent
        self.message_promises = message_promises

        self._parent: Optional["InteractionContext"] = None
        self._reply_streamer = reply_streamer
        self._tasks_to_wait_for: list[Awaitable[Any]] = []
        self._child_agent_calls: set[AgentCall] = set()
        self._previous_ctx_token: Optional[contextvars.Token] = None

    def get_agent_trace(self) -> list["MiniAgent"]:
        trace = []
        ctx = self
        while ctx:
            trace.append(ctx.this_agent)
            ctx = ctx._parent  # pylint: disable=protected-access
        return trace

    @classmethod
    def get_current(cls) -> "InteractionContext":
        current = cls._current.get()
        if not current:
            raise NoActiveContextError(f"No {cls.__name__} is currently active.")
        return current

    def reply(self, messages: MessageType) -> None:
        """
        Send a reply to the messages that were received by the agent. The messages can be of any allowed MessageType.
        They will be converted to Message objects when they arrive at the agent that made a call to the current agent.

        ATTENTION! If an async iterator is passed as `messages`, it will not be iterated over immediately and its
        content will not be "frozen" exactly at the moment it was passed (they way regular iterables and other types
        would).
        """
        self._reply_streamer.append(messages)

    def make_sure_to_wait(self, awaitable: Awaitable[Any], start_soon_if_coroutine: bool = True) -> None:
        """
        Make sure to wait for the completion of the provided awaitable before exiting the current agent call and
        closing the reply sequence.
        """
        if asyncio.iscoroutine(awaitable) and start_soon_if_coroutine:
            # let's turn this coroutine into our special kind of task and start it as soon as possible
            awaitable = MiniAgents.get_current().start_soon(awaitable)
        self._tasks_to_wait_for.append(awaitable)

    async def await_now(self) -> None:
        """
        Wait for all the awaitables that were fed into the `make_sure_to_wait` method to finish. If this method is not
        called in the agent explicitly, then all such awaitables will be awaited for automatically before the agent's
        reply sequence is closed.
        """
        if any(not call.is_finished for call in self._child_agent_calls):
            warnings.warn(
                "Potential deadlock detected: unfinished agent call(s) encountered. "
                "Make sure to call .finish() on all AgentCall objects or use reply_sequence() "
                "with finish_call=True (default) to avoid deadlocks.",
                RuntimeWarning,
                stacklevel=2,
            )

        await asyncio.gather(*self._tasks_to_wait_for, return_exceptions=True)

    async def afinish_early(self, make_sure_to_wait: bool = True) -> None:
        if make_sure_to_wait:
            await self.await_now()
        self._reply_streamer.close()

    def _activate(self) -> None:
        self._parent = self._current.get()
        if self._previous_ctx_token:
            raise RuntimeError(f"{type(self).__name__} is not reentrant")
        self._previous_ctx_token = self._current.set(self)  # <- this is the context switch

    async def _afinalize(self) -> None:
        for agent_call in self._child_agent_calls:
            agent_call.finish()
        await self.await_now()
        self._current.reset(self._previous_ctx_token)
        self._previous_ctx_token = None


# noinspection PyProtectedMember
class AgentCall:  # pylint: disable=protected-access
    def __init__(
        self,
        message_streamer: MessageSequenceAppender,
        reply_sequence_promise: MessageSequencePromise,
    ) -> None:
        self._message_streamer = message_streamer
        self._reply_sequence_promise = reply_sequence_promise

        self._message_streamer.open()

        try:
            InteractionContext.get_current()._child_agent_calls.add(self)
        except NoActiveContextError:
            MiniAgents.get_current()._child_agent_calls.add(self)

    def send_message(self, messages: MessageType) -> "AgentCall":
        """
        Send a zero or more input messages to the agent.

        ATTENTION! If an async iterator is passed as `messages`, it will not be iterated over immediately and its
        content will not be "frozen" exactly at the moment it was passed (they way regular iterables and other types
        would).
        """
        self._message_streamer.append(messages)
        return self

    def reply_sequence(self, finish_call: bool = True) -> MessageSequencePromise:
        """
        Get a promise of a reply sequence by the agent. If `finish_call` is True (the default), then,
        after this method is called, it is not possible to send any more requests to this AgentCall object.

        ATTENTION! Set `finish_call` to False only if you know what you are doing. It is easy to create
        deadlocks when `finish_call` is set to False!
        """
        if finish_call:
            self.finish()
        return self._reply_sequence_promise

    def finish(self) -> "AgentCall":
        """
        Finish the agent call.

        NOTE: After this method is called it is not possible to send any more requests to this AgentCall object.
        """
        self._message_streamer.close()
        try:
            InteractionContext.get_current()._child_agent_calls.discard(self)
        except NoActiveContextError:
            MiniAgents.get_current()._child_agent_calls.discard(self)
        return self

    @property
    def is_finished(self) -> bool:
        """
        Return True if the agent call is finished, which means that no more messages can be sent to it.

        NOTE: It doesn't matter whether the agent has finished replying or not. The agent that was called can still
        produce replies, even after the call was "finished". The replies will be delivered via the promise of a reply
        sequence, which is a separate object (see `reply_sequence()`).
        """
        return not self._message_streamer.is_open


class AgentInteractionNode(Message):
    agent: MiniAgent


class AgentCallNode(AgentInteractionNode):
    messages: tuple[Message, ...]


class AgentReplyNode(AgentInteractionNode):
    agent_call: AgentCallNode
    replies: tuple[Message, ...]


# noinspection PyProtectedMember
class AgentReplyMessageSequence(MessageSequence):
    # pylint: disable=protected-access
    def __init__(
        self,
        mini_agent: MiniAgent,
        input_sequence_promise: MessageSequencePromise,
        kwargs_to_freeze: dict[str, Any],
        **kwargs,
    ) -> None:
        self._frozen_kwargs = Frozen(**kwargs_to_freeze).as_kwargs()

        self._mini_agent = mini_agent
        self._input_sequence_promise = input_sequence_promise
        super().__init__(
            appender_capture_errors=True,  # we want `self.message_appender` not to let errors out of `run_the_agent`
            **kwargs,
        )

    async def _streamer(self, _) -> AsyncIterator[MessagePromise]:
        async def run_the_agent(_) -> AgentCallNode:
            ctx = InteractionContext(
                this_agent=self._mini_agent,
                message_promises=self._input_sequence_promise,
                reply_streamer=self.message_appender,
            )
            with self.message_appender:
                # errors are not raised above this `with` block, thanks to `appender_capture_errors=True`
                try:
                    ctx._activate()

                    kwargs = {
                        **self._mini_agent._static_kwargs,
                        **self._mini_agent._mutable_state,
                        **self._frozen_kwargs,
                    }
                    if isinstance(self._mini_agent._func_or_class, type):
                        # the miniagent is defined as a class, not as a function -> let's create an instance of this
                        # class and call its `__call__` method
                        actual_func = self._mini_agent._func_or_class(
                            # if we want Pydantic models to also be used as class-based agents, we can't pass
                            # `ctx` as a positional argument (BaseModel's `__init__` doesn't accept positional
                            # arguments)
                            ctx=ctx,
                            **kwargs,
                        )
                        await actual_func()
                    else:
                        # the miniagent is a function
                        await self._mini_agent._func_or_class(ctx, **kwargs)
                except Exception as e:
                    PromisingContext.get_current()._log_background_error_once(e)
                    raise
                finally:
                    await ctx._afinalize()

            return AgentCallNode(  # TODO why not "persist" this node before the agent function finishes ?
                messages=await self._input_sequence_promise,
                agent=self._mini_agent,
                **dict(self._mini_agent.interaction_metadata),
                # TODO **self._mini_agent._static_kwargs ?
                # TODO **self._mini_agent._mutable_state ?
                **self._frozen_kwargs,
            )

        agent_call_promise = Promise[AgentCallNode](
            start_soon=True,
            resolver=run_the_agent,
        )

        async for reply_promise in super()._streamer(_):
            yield reply_promise  # at this point all MessageType items are "flattened" into MessagePromise items

        async def create_agent_reply_node(_) -> AgentReplyNode:
            return AgentReplyNode(
                replies=await self.sequence_promise,
                agent=self._mini_agent,
                agent_call=await agent_call_promise,
                **dict(self._mini_agent.interaction_metadata),
            )

        Promise[AgentReplyNode](
            start_soon=True,  # use a separate async task to avoid deadlock upon AgentReplyNode resolution
            resolver=create_agent_reply_node,
        )
