"""
"Core" classes of the MiniAgents framework.
"""

import asyncio
import contextvars
import inspect
import logging
import re
import warnings
from contextvars import ContextVar
from importlib.metadata import version, PackageNotFoundError
from typing import Any, AsyncIterator, Awaitable, Callable, Iterable, Optional, Union

from pydantic import Field

from miniagents.messages import (
    Message,
    MessagePromise,
    MessageSequence,
    MessageSequenceAppender,
    MessageSequencePromise,
)
from miniagents.miniagent_typing import AgentFunction, MessageType, PersistMessagesEventHandler
from miniagents.promising.errors import NoActiveContextError, WrongActiveContextError
from miniagents.promising.ext.frozen import Frozen
from miniagents.promising.promise_typing import PromiseResolvedEventHandler
from miniagents.promising.promising import Promise, PromisingContext
from miniagents.promising.sentinels import NO_VALUE, Sentinel
from miniagents.utils import MiniAgentsLogFormatter

try:
    __version__ = version("MiniAgents")
except PackageNotFoundError:
    __version__ = "0.0.0"  # fallback or default for dev environments


_default_logger = logging.Logger("MiniAgents", level=logging.WARNING)
_log_formatter = MiniAgentsLogFormatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
_log_handler = logging.StreamHandler()
_log_handler.setFormatter(_log_formatter)
_default_logger.addHandler(_log_handler)


class MiniAgents(PromisingContext):
    stream_llm_tokens_by_default: bool
    llm_logger_agent: Union["MiniAgent", bool]
    on_persist_messages_handlers: list[PersistMessagesEventHandler]
    errors_as_messages: bool
    error_tracebacks_in_messages: bool
    log_reduced_tracebacks: bool
    await_reply_persistence_before_agent_finish: bool

    logger: logging.Logger = _default_logger

    def __init__(
        self,
        *,
        stream_llm_tokens_by_default: bool = True,
        llm_logger_agent: Union["MiniAgent", bool] = False,
        on_persist_messages: Union[PersistMessagesEventHandler, Iterable[PersistMessagesEventHandler]] = (),
        on_promise_resolved: Union[PromiseResolvedEventHandler, Iterable[PromiseResolvedEventHandler]] = (),
        errors_as_messages: bool = False,
        error_tracebacks_in_messages: bool = False,
        log_reduced_tracebacks: bool = True,
        await_reply_persistence_before_agent_finish: bool = False,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ) -> None:
        on_promise_resolved = (
            [self._atrigger_persist_messages_event, on_promise_resolved]
            if callable(on_promise_resolved)
            else [self._atrigger_persist_messages_event, *on_promise_resolved]
        )
        super().__init__(on_promise_resolved=on_promise_resolved, logger=logger, **kwargs)

        self.errors_as_messages = errors_as_messages  # TODO should this propagate to all child agent calls if set ?
        self.error_tracebacks_in_messages = error_tracebacks_in_messages
        self.log_reduced_tracebacks = log_reduced_tracebacks
        self.stream_llm_tokens_by_default = stream_llm_tokens_by_default
        self.llm_logger_agent = llm_logger_agent
        self.await_reply_persistence_before_agent_finish = await_reply_persistence_before_agent_finish
        self.on_persist_messages_handlers: list[PersistMessagesEventHandler] = (
            [on_persist_messages] if callable(on_persist_messages) else list(on_persist_messages)
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

    def on_persist_messages(self, handler: PersistMessagesEventHandler) -> PersistMessagesEventHandler:
        """
        Add a handler that will be called every time a Message needs to be persisted.
        """
        if not callable(handler):
            raise ValueError("An `on_persist_messages` handler must be a callable.")
        if not inspect.iscoroutinefunction(handler):
            raise ValueError("An `on_persist_messages` handler must be async.")

        self.on_persist_messages_handlers.append(handler)
        return handler

    # noinspection PyProtectedMember
    async def apersist_messages(
        self,
        message_or_messages: Union[Message, Iterable[Message]],
        extend_with_sub_messages: bool = True,
        parallelise_handlers: bool = False,
        raise_on_error: bool = True,
    ) -> list[Message]:
        """
        Persists the given message or messages using the registered `on_persist_messages` handlers.

        This method is typically called automatically when a MessagePromise is resolved (which typically
        happens in the background when agents communicate with each other). However, it can also be called
        manually if needed (e.g. you want to persist multiple messages to a database and do that in a single
        database transaction that you opened).

        Args:
            message_or_messages: A single `Message` object or an iterable of `Message` objects to persist.
            extend_with_sub_messages: If True (default), all sub-messages of the given messages (no matter the
                depth of nesting) will also be persisted. This is useful when a message is a container for other,
                nested messages.
            parallelise_handlers: If True, the `on_persist_messages` handlers will be called in parallel.
                Defaults to False, meaning the handlers will be called sequentially.
            raise_on_error: If True (default), an exception will be raised if any of the handlers raises an exception.

        Returns:
            A list of messages that were actually persisted (there is a mechanism that prevents persisting the same
            message more than once).

        NOTE: If your objective is to persist messages in a single database transaction, you probably should not
        parallelise the handlers (you should keep `parallelise_handlers=False`), otherwise they will be run as
        separate async operations and most likely not be part of the transaction you opened.
        """
        # pylint: disable=protected-access,broad-exception-caught
        if isinstance(message_or_messages, Message):
            message_or_messages = [message_or_messages]

        messages_to_persist = []
        acquired_locks = []

        async def _is_persistence_not_needed(message: Message) -> bool:
            if message.persistence_not_needed:
                return True

            await message._persistence_lock.acquire()
            if message.persistence_not_needed:
                message._persistence_lock.release()
                return True

            acquired_locks.append(message._persistence_lock)
            return False

        async def _apersist_messages() -> None:
            if parallelise_handlers:
                parallel_handlers = []
                for handler in self.on_persist_messages_handlers:
                    parallel_handlers.append(self.start_soon(handler(messages_to_persist)))
                await self.agather(*parallel_handlers, return_exceptions=not raise_on_error)
            else:
                for handler in self.on_persist_messages_handlers:
                    try:
                        await handler(messages_to_persist)
                    except Exception as e:
                        if raise_on_error:
                            raise e
                        self.logger.debug("ERROR PERSISTING MESSAGES", exc_info=True)

        try:
            for message in message_or_messages:
                if not isinstance(message, Message):
                    raise ValueError("The messages must be of type Message.")

                if await _is_persistence_not_needed(message):
                    continue

                if extend_with_sub_messages:
                    for sub_message in message.sub_messages():
                        if await _is_persistence_not_needed(sub_message):
                            continue

                        messages_to_persist.append(sub_message)

                messages_to_persist.append(message)

            await _apersist_messages()
            return messages_to_persist
        finally:
            for message in messages_to_persist:
                message._persistence_not_needed = True

            for lock in acquired_locks:
                lock.release()

    async def afinalize(self) -> None:
        for agent_call in list(self._child_agent_calls):
            agent_call.finish()
        await super().afinalize()

    async def _atrigger_persist_messages_event(self, _, obj: Any) -> None:
        if not isinstance(obj, Message):
            return

        await self.apersist_messages(obj, extend_with_sub_messages=True, parallelise_handlers=True)


def miniagent(
    func_or_class: Optional[Union[AgentFunction, type]] = None,
    *,
    alias: Optional[str] = None,
    description: Optional[str] = None,
    normalize_func_or_class_name: bool = True,
    normalize_spaces_in_docstring: bool = True,
    await_reply_persistence: Union[bool, Sentinel] = NO_VALUE,
    interaction_metadata: Optional[dict[str, Any]] = None,
    non_freezable_kwargs: Optional[dict[str, Any]] = None,
    **kwargs_to_freeze,
) -> Union["MiniAgent", Callable[[AgentFunction], "MiniAgent"]]:
    """
    A decorator that converts an agent function into an agent.

    # TODO describe parameters
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
                await_reply_persistence=await_reply_persistence,
                interaction_metadata=interaction_metadata,
                non_freezable_kwargs=non_freezable_kwargs,
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
        await_reply_persistence=await_reply_persistence,
        interaction_metadata=interaction_metadata,
        non_freezable_kwargs=non_freezable_kwargs,
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
        normalize_func_or_class_name: bool = True,
        normalize_spaces_in_docstring: bool = True,
        await_reply_persistence: Union[bool, Sentinel] = NO_VALUE,
        interaction_metadata: Optional[Union[dict[str, Any], Frozen]] = None,
        non_freezable_kwargs: Optional[dict[str, Any]] = None,
        **kwargs_to_freeze,
    ) -> None:
        if not callable(func_or_class):
            raise ValueError("A `@miniagent` decorated type must be a callable.")
        if not inspect.iscoroutinefunction(func_or_class) and not (
            hasattr(func_or_class, "__call__") and inspect.iscoroutinefunction(func_or_class.__call__)
        ):
            raise ValueError("A `@miniagent` decorated class or function must be async.")

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

        super().__init__(
            alias=alias,
            description=description,
            interaction_metadata=interaction_metadata,
        )
        self.__name__ = alias
        self.__doc__ = description

        self._func_or_class = func_or_class
        self._frozen_kwargs = Frozen(**kwargs_to_freeze).as_kwargs()
        self._non_freezable_kwargs = dict(non_freezable_kwargs or {})
        self._await_reply_persistence = await_reply_persistence

    def trigger(
        self,
        messages: Optional[MessageType] = None,
        start_soon: Union[bool, Sentinel] = NO_VALUE,
        errors_as_messages: Union[bool, Sentinel] = NO_VALUE,
        **kwargs_to_freeze,
    ) -> MessageSequencePromise:
        agent_call = self.initiate_call(
            start_soon=start_soon, errors_as_messages=errors_as_messages, **kwargs_to_freeze
        )
        if messages is not None:
            agent_call.send_message(messages)
        return agent_call.reply_sequence()

    # noinspection PyProtectedMember
    def initiate_call(
        self,
        start_soon: Union[bool, Sentinel] = NO_VALUE,
        errors_as_messages: Union[bool, Sentinel] = NO_VALUE,
        **kwargs_to_freeze,
    ) -> "AgentCall":
        """
        Start a call with the agent. The agent will be called with the provided function kwargs.
        TODO expand this docstring ?
        """
        input_sequence = MessageSequence(start_soon=False, errors_as_messages=False)
        reply_sequence = AgentReplyMessageSequence(
            mini_agent=self,
            kwargs_to_freeze=kwargs_to_freeze,
            input_sequence_promise=input_sequence.sequence_promise,
            start_soon=start_soon,
            errors_as_messages=errors_as_messages,
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
        non_freezable_kwargs: Optional[dict[str, Any]] = None,
        **kwargs_to_freeze,
    ) -> Union["MiniAgent", Callable[[AgentFunction], "MiniAgent"]]:
        """
        Create a forked version of this agent with modified parameters.

        Args:
            alias: New alias for the forked agent. If not provided, uses the original alias.
            description: New description for the forked agent. If not provided, uses the original description.
            interaction_metadata: TODO explain this parameter
            non_freezable_kwargs: Additional non-freezable kwargs to merge with the original non-freezable kwargs.
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
            non_freezable_kwargs={**self._non_freezable_kwargs, **(non_freezable_kwargs or {})},
            **self._frozen_kwargs,
            **kwargs_to_freeze,
        )

    @property
    def wrapped_func_or_class(self) -> Union[AgentFunction, type]:
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
    miniagents: MiniAgents

    _current: ContextVar[Optional["InteractionContext"]] = ContextVar("InteractionContext._current", default=None)

    def __init__(
        self,
        this_agent: "MiniAgent",
        message_promises: MessageSequencePromise,
        reply_streamer: MessageSequenceAppender,
    ) -> None:
        self.miniagents = MiniAgents.get_current()
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

    def reply(self, messages: MessageType, out_of_order: bool = False) -> "InteractionContext":
        """
        Send zero or more response messages to the calling agent. The messages can be of any allowed `MessageType`
        (see `miniagent_typing.py`). They will be converted to `Message` objects after they arrive at the
        calling agent and the calling agent `awaits` for their respective promises.

        ATTENTION! If an async iterator is passed as `messages`, it will not be iterated over immediately and its
        content will not be "frozen" exactly at the moment it was passed (they way regular iterables and other types
        would).
        """
        # TODO make it possible to send additional attributes through kwargs
        #  if there are no concrete messages, message promises or async iterators ?
        #  (will there be any confusion in regards to how kwargs are used in `trigger`, though ?)
        # TODO set agent_alias attribute automatically
        #  if there are no concrete messages, message promises or async iterators ?
        self._reply_streamer.append(messages, out_of_order=out_of_order)
        return self

    def reply_out_of_order(self, messages: MessageType) -> "InteractionContext":
        """
        Send zero or more response messages to the calling agent. The messages can be of any allowed `MessageType` (see
        `miniagent_typing.py`). They will be converted to `Message` objects after they arrive at the calling agent and
        the calling agent `awaits` for their respective promises.

        NOTE: Unlike `reply()`, these response messages are treated as unordered and will bypass the usual message
        ordering in the resulting sequence as much as possible. This means that they will be delivered earlier than
        some other messages which were sent before them but aren't available yet (e.g. a sequence that is coming from
        some other agent and was already placed into the response sequence of this agent but is not yet complete).

        ATTENTION! If an async iterator is passed as `messages`, it will not be iterated over immediately and its
        content will not be "frozen" exactly at the moment it was passed (they way regular iterables and other types
        would).
        """
        # TODO make it possible to send additional attributes through kwargs
        #  if there are no concrete messages, message promises or async iterators ?
        #  (will there be any confusion in regards to how kwargs are used in `trigger`, though ?)
        # TODO set agent_alias attribute automatically
        #  if there are no concrete messages, message promises or async iterators ?
        return self.reply(messages, out_of_order=True)

    def make_sure_to_wait(self, awaitable: Awaitable[Any], start_soon_if_coroutine: bool = True) -> None:
        """
        Make sure to wait for the completion of the provided awaitable before exiting the current agent call and
        closing the reply sequence.
        """
        if asyncio.iscoroutine(awaitable) and start_soon_if_coroutine:
            # let's turn this coroutine into our special kind of task and start it as soon as possible
            awaitable = self.miniagents.start_soon(awaitable)
        self._tasks_to_wait_for.append(awaitable)

    async def await_now(self, suppress_deadlock_warning: bool = False) -> None:
        """
        Wait for all the awaitables that were fed into the `make_sure_to_wait` method to finish. If this method is not
        called in the agent explicitly, then all such awaitables will be awaited for automatically before the agent's
        reply sequence is closed.
        """
        if not suppress_deadlock_warning and any(not call.is_finished for call in self._child_agent_calls):
            warnings.warn(
                "Potential deadlock detected: unfinished agent call(s) encountered. "
                "Make sure to call `finish()` on all `AgentCall` objects or use `reply_sequence()` "
                "with `finish_call=True` (default) to avoid potential deadlocks.\n"
                "\n"
                "A deadlock is possible if a certain agent's response is registered to be awaited for and "
                "`await_now()` is called before the corresponding `AgentCall` is finished (this would lead to both "
                "waiting for each other). Use `suppress_deadlock_warning=True` to suppress this warning if you are "
                "sure that this is not the case.\n",
                RuntimeWarning,
                stacklevel=2,
            )

        await self.miniagents.agather(*self._tasks_to_wait_for)

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
        for agent_call in list(self._child_agent_calls):
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

        self._mini_agents = MiniAgents.get_current()
        try:
            InteractionContext.get_current()._child_agent_calls.add(self)
        except NoActiveContextError:
            self._mini_agents._child_agent_calls.add(self)

    def send_message(self, messages: MessageType, out_of_order: bool = False) -> "AgentCall":
        """
        Send zero or more input messages to the agent.

        ATTENTION! If an async iterator is passed as `messages`, it will not be iterated over immediately and its
        content will not be "frozen" exactly at the moment it was passed (they way regular iterables and other types
        would).
        """
        # TODO make it possible to send additional attributes through kwargs
        #  if there are no concrete messages, message promises or async iterators ?
        #  (will there be any confusion in regards to how kwargs are used in `trigger`, though ?)
        # TODO set agent_alias attribute automatically
        #  if there are no concrete messages, message promises or async iterators ?
        self._message_streamer.append(messages, out_of_order=out_of_order)
        return self

    def send_out_of_order(self, messages: MessageType) -> "AgentCall":
        """
        Send zero or more input messages to the agent.

        NOTE: Unlike `send_message()`, these input messages are treated as unordered and will bypass the usual message
        ordering in the resulting sequence as much as possible. This means that they will be delivered earlier than
        some other messages which were sent before them but aren't available yet (e.g. a sequence that is coming from
        some other agent and was already placed into the message sequence for this agent but is not yet complete).

        ATTENTION! If an async iterator is passed as `messages`, it will not be iterated over immediately and its
        content will not be "frozen" exactly at the moment it was passed (they way regular iterables and other types
        would).
        """
        # TODO make it possible to send additional attributes through kwargs
        #  if there are no concrete messages, message promises or async iterators ?
        #  (will there be any confusion in regards to how kwargs are used in `trigger`, though ?)
        # TODO set agent_alias attribute automatically
        #  if there are no concrete messages, message promises or async iterators ?
        return self.send_message(messages, out_of_order=True)

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
            self._mini_agents._child_agent_calls.discard(self)
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
            appender_capture_errors=True,  # we want `self.message_appender` not to let errors out of `_arun_agent`
            **kwargs,
        )

    async def _astreamer(self, _) -> AsyncIterator[MessagePromise]:
        async def _arun_agent(_) -> AgentCallNode:
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
                        **self._mini_agent._frozen_kwargs,
                        **self._mini_agent._non_freezable_kwargs,
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
                    MiniAgents.get_current()._log_background_error_once(
                        e,
                        # if `errors_as_messages` is True, we don't want to log the error, we treat it as "just another
                        # message" in that case
                        fake_log=self._errors_as_messages,
                    )
                    raise
                finally:
                    await ctx._afinalize()

            return AgentCallNode(  # TODO why not "persist" this node before the agent function finishes ?
                messages=await self._input_sequence_promise,
                agent=self._mini_agent,
                **dict(self._mini_agent.interaction_metadata),
                # TODO **self._mini_agent._frozen_kwargs ?
                # TODO **self._mini_agent._non_freezable_kwargs ?
                **self._frozen_kwargs,
            )

        agent_call_promise = Promise[AgentCallNode](
            start_soon=True,
            resolver=_arun_agent,
        )

        await_reply_persistence = self._mini_agent._await_reply_persistence
        if await_reply_persistence is NO_VALUE:
            await_reply_persistence = MiniAgents.get_current().await_reply_persistence_before_agent_finish

        reply_promises = []
        async for reply_promise in super()._astreamer(_):
            yield reply_promise  # at this point all MessageType items are "flattened" into MessagePromise items
            if await_reply_persistence:
                reply_promises.append(reply_promise)

        if await_reply_persistence:
            # There will be a certain level of chaos in regards to persistence batching - some messages will manage to
            # be persisted individually upon their "resolution" (in batches together with their own sub-messages),
            # others will be persisted by the method call below (which will happen in a single batch for all those
            # remaining messages).
            # TODO Should we do something about this ?
            await MiniAgents.get_current().apersist_messages([await reply_promise for reply_promise in reply_promises])

        async def _acreate_agent_reply_node(_) -> AgentReplyNode:
            return AgentReplyNode(
                replies=await self.sequence_promise,
                agent=self._mini_agent,
                agent_call=await agent_call_promise,
                **dict(self._mini_agent.interaction_metadata),
            )

        Promise[AgentReplyNode](
            start_soon=True,  # use a separate async task to avoid deadlock upon AgentReplyNode resolution
            resolver=_acreate_agent_reply_node,
        )
