"""
"Core" classes of the MiniAgents framework.
"""

import asyncio
import contextvars
import logging
import re
from contextvars import ContextVar
from typing import AsyncIterator, Any, Union, Optional, Callable, Iterable, Awaitable

from pydantic import BaseModel, Field

from miniagents.messages import MessagePromise, MessageSequencePromise, Message
from miniagents.miniagent_typing import MessageType, AgentFunction, PersistMessageEventHandler
from miniagents.promising.errors import NoActiveContextError, WrongActiveContextError
from miniagents.promising.ext.frozen import Frozen
from miniagents.promising.promise_typing import PromiseStreamer, PromiseResolvedEventHandler
from miniagents.promising.promising import StreamAppender, Promise, PromisingContext
from miniagents.promising.sequence import FlatSequence
from miniagents.utils import ReducedTracebackFormatter


class MiniAgents(PromisingContext):
    """
    TODO Oleksandr: docstring
    """

    stream_llm_tokens_by_default: bool
    llm_logger_agent: Union["MiniAgent", bool]
    normalize_agent_func_and_class_names: bool
    normalize_spaces_in_agent_docstrings: bool
    on_persist_message_handlers: list[PersistMessageEventHandler]
    log_reduced_tracebacks: bool

    def __init__(
        self,
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
        if not logger:
            logger = logging.getLogger("MiniAgents")
            formatter_class = ReducedTracebackFormatter if log_reduced_tracebacks else logging.Formatter
            formatter = formatter_class(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        super().__init__(on_promise_resolved=on_promise_resolved, logger=logger, **kwargs)

        self.stream_llm_tokens_by_default = stream_llm_tokens_by_default
        self.llm_logger_agent = llm_logger_agent
        self.normalize_agent_func_and_class_names = normalize_agent_func_and_class_names
        self.normalize_spaces_in_agent_docstrings = normalize_spaces_in_agent_docstrings
        self.on_persist_message_handlers: list[PersistMessageEventHandler] = (
            [on_persist_message] if callable(on_persist_message) else list(on_persist_message)
        )

        self._child_agent_calls: set[AgentCall] = set()

    def run(self, awaitable: Awaitable[Any]) -> Any:
        """
        Run an awaitable in the MiniAgents context. This method is blocking. It also creates a new event loop.
        """
        return asyncio.run(self.arun(awaitable))

    async def arun(self, awaitable: Awaitable[Any]) -> Any:
        """
        Run an awaitable in the MiniAgents context.
        """
        async with self:
            return await awaitable

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
                self.start_asap(handler(_, sub_message))
            sub_message._persist_message_event_triggered = True

        if obj._persist_message_event_triggered:
            return

        for handler in self.on_persist_message_handlers:
            self.start_asap(handler(_, obj))
        obj._persist_message_event_triggered = True


def miniagent(
    func_or_class: Optional[Union[AgentFunction, type]] = None,
    alias: Optional[str] = None,
    description: Optional[str] = None,
    normalize_func_or_class_name: bool = True,
    normalize_spaces_in_docstring: bool = True,
    interaction_metadata: Optional[dict[str, Any]] = None,
    mutable_kwargs: Optional[dict[str, Any]] = None,
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
                mutable_kwargs=mutable_kwargs,
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
        mutable_kwargs=mutable_kwargs,
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
        alias: Optional[str] = None,
        description: Optional[str] = None,
        normalize_func_or_class_name: Optional[bool] = None,
        normalize_spaces_in_docstring: Optional[bool] = None,
        interaction_metadata: Optional[Union[dict[str, Any], Frozen]] = None,
        mutable_kwargs: Optional[dict[str, Any]] = None,
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
        # TODO Oleksandr: is `interaction_metadata` a good name ? see how it is used in Recensia to decide
        interaction_metadata = Frozen(**dict(interaction_metadata or {}))

        super().__init__(alias=alias, description=description, interaction_metadata=interaction_metadata)
        self.__name__ = alias
        self.__doc__ = description

        self._func_or_class = func_or_class
        self._static_kwargs = dict(mutable_kwargs or {})
        self._static_kwargs.update(Frozen(**kwargs_to_freeze).as_kwargs())

    def inquire(
        self, messages: Optional[MessageType] = None, start_asap: Optional[bool] = None, **kwargs_to_freeze
    ) -> MessageSequencePromise:
        """
        TODO Oleksandr: docstring
        """
        agent_call = self.initiate_inquiry(start_asap=start_asap, **kwargs_to_freeze)
        if messages is not None:
            agent_call.send_message(messages)
        return agent_call.reply_sequence()

    def kick_off(self, messages: Optional[MessageType] = None, **kwargs_to_freeze) -> None:
        """
        Make a call to the agent and ignore the response.
        """
        self.inquire(messages, start_asap=True, **kwargs_to_freeze)

    # noinspection PyProtectedMember
    def initiate_inquiry(self, start_asap: Optional[bool] = None, **kwargs_to_freeze) -> "AgentCall":
        """
        Start an inquiry with the agent. The agent will be called with the provided function kwargs.
        TODO Oleksandr: expand this docstring ?
        """
        input_sequence = MessageSequence(
            start_asap=False,
        )
        reply_sequence = AgentReplyMessageSequence(
            mini_agent=self,
            kwargs_to_freeze=kwargs_to_freeze,
            input_sequence_promise=input_sequence.sequence_promise,
            start_asap=start_asap,
        )

        agent_call = AgentCall(
            message_streamer=input_sequence.message_appender,
            reply_sequence_promise=reply_sequence.sequence_promise,
        )
        return agent_call

    def fork(
        self,
        alias: Optional[str] = None,  # TODO Oleksandr: enforce unique aliases ? introduce some "fork identifier" ?
        description: Optional[str] = None,
        interaction_metadata: Optional[Union[dict[str, Any], Frozen]] = None,
        mutable_kwargs: Optional[dict[str, Any]] = None,
        **kwargs_to_freeze,
    ) -> Union["MiniAgent", Callable[[AgentFunction], "MiniAgent"]]:
        """
        TODO Oleksandr: docstring
        """
        return MiniAgent(
            self._func_or_class,
            alias=alias or self.alias,
            description=description or self.description,
            normalize_func_or_class_name=False,
            normalize_spaces_in_docstring=False,
            interaction_metadata={**dict(self.interaction_metadata), **dict(interaction_metadata or {})},
            mutable_kwargs=mutable_kwargs,
            **self._static_kwargs,
            **kwargs_to_freeze,
        )


class InteractionContext:
    """
    TODO Oleksandr: docstring
    """

    this_agent: MiniAgent
    message_promises: MessageSequencePromise

    _current: ContextVar[Optional["InteractionContext"]] = ContextVar("InteractionContext._current", default=None)

    def __init__(
        self,
        this_agent: "MiniAgent",
        message_promises: MessageSequencePromise,
        reply_streamer: "MessageSequenceAppender",
    ) -> None:
        self.this_agent = this_agent
        self.message_promises = message_promises
        self._reply_streamer = reply_streamer
        self._tasks_to_wait_for: list[Awaitable[Any]] = []
        self._child_agent_calls: set[AgentCall] = set()
        self._previous_ctx_token: Optional[contextvars.Token] = None

    @classmethod
    def get_current(cls) -> "InteractionContext":
        """
        TODO Oleksandr: docstring
        """
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

    def wait_for(self, awaitable: Awaitable[Any], start_asap_if_coroutine: bool = True) -> None:
        """
        Make sure to wait for the completion of the provided awaitable before exiting the current agent call and
        closing the reply sequence.
        """
        if asyncio.iscoroutine(awaitable) and start_asap_if_coroutine:
            # let's turn this coroutine into our special kind of task and start it as soon as possible
            awaitable = MiniAgents.get_current().start_asap(awaitable)
        self._tasks_to_wait_for.append(awaitable)

    async def await_for_subtasks(self) -> None:
        """
        Wait for all the awaitables that were fed into the `wait_for` method to finish. If this method is not called
        in the agent explicitly, then all such awaitables will be awaited for automatically before the agent's reply
        sequence is closed.
        """
        # TODO Oleksandr: What if one of the subtasks represents an unfinished agent call ? How should we make it
        #  obvious to the user that the reason they are experiencing a deadlock is because they forgot to finish an
        #  agent call ?
        await asyncio.gather(*self._tasks_to_wait_for, return_exceptions=True)

    async def afinish_early(self, await_for_subtasks: bool = True) -> None:
        """
        TODO Oleksandr: docstring
        """
        if await_for_subtasks:
            await self.await_for_subtasks()
        self._reply_streamer.close()

    def _activate(self) -> None:
        """
        TODO Oleksandr: docstring
        """
        if self._previous_ctx_token:
            raise RuntimeError(f"{type(self).__name__} is not reentrant")
        self._previous_ctx_token = self._current.set(self)  # <- this is the context switch

    async def _afinalize(self) -> None:
        """
        TODO Oleksandr: docstring
        """
        for agent_call in self._child_agent_calls:
            agent_call.finish()
        await self.await_for_subtasks()
        self._current.reset(self._previous_ctx_token)
        self._previous_ctx_token = None


# noinspection PyProtectedMember
class AgentCall:  # pylint: disable=protected-access
    """
    TODO Oleksandr: docstring
    """

    def __init__(
        self,
        message_streamer: "MessageSequenceAppender",
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

    def reply_sequence(self, close_request_sequence: bool = True) -> MessageSequencePromise:
        """
        Get a promise of a reply sequence by the agent. If `close_request_sequence` is True (the default), then,
        after this method is called, it is not possible to send any more requests to this AgentCall object.

        ATTENTION! Set `close_request_sequence` to False only if you know what you are doing. It is easy to create
        deadlocks when `close_request_sequence` is set to False!
        """
        if close_request_sequence:
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


class AgentInteractionNode(Message):
    """
    TODO Oleksandr: docstring
    """

    agent: MiniAgent


class AgentCallNode(AgentInteractionNode):
    """
    TODO Oleksandr: docstring
    """

    messages: tuple[Message, ...]


class AgentReplyNode(AgentInteractionNode):
    """
    TODO Oleksandr: docstring
    """

    agent_call: AgentCallNode
    replies: tuple[Message, ...]


class MessageSequence(FlatSequence[MessageType, MessagePromise]):
    """
    TODO Oleksandr: docstring
    """

    message_appender: Optional["MessageSequenceAppender"]
    sequence_promise: MessageSequencePromise

    def __init__(
        self,
        appender_capture_errors: Optional[bool] = None,
        start_asap: Optional[bool] = None,
        incoming_streamer: Optional[PromiseStreamer[MessageType]] = None,
    ) -> None:
        if incoming_streamer:
            # an external streamer is provided, so we don't create the default StreamAppender
            self.message_appender = None
        else:
            self.message_appender = MessageSequenceAppender(capture_errors=appender_capture_errors)
            incoming_streamer = self.message_appender

        super().__init__(
            incoming_streamer=incoming_streamer,
            start_asap=start_asap,
            sequence_promise_class=MessageSequencePromise,
        )

    @classmethod
    def turn_into_sequence_promise(cls, messages: MessageType) -> MessageSequencePromise:
        """
        Convert an arbitrarily nested collection of messages of various types (strings, dicts, Message objects,
        MessagePromise objects etc. - see `MessageType` definition for details) into a flat and uniform
        MessageSequencePromise object.
        """
        message_sequence = cls(
            appender_capture_errors=True,
            start_asap=False,
        )
        with message_sequence.message_appender:
            message_sequence.message_appender.append(messages)
        return message_sequence.sequence_promise

    async def _flattener(  # pylint: disable=invalid-overridden-method
        self, zero_or_more_items: MessageType
    ) -> AsyncIterator[MessagePromise]:
        if isinstance(zero_or_more_items, MessagePromise):
            yield zero_or_more_items
        elif isinstance(zero_or_more_items, Message):
            yield zero_or_more_items.as_promise
        elif isinstance(zero_or_more_items, BaseModel):
            yield Message(**dict(zero_or_more_items)).as_promise
        elif isinstance(zero_or_more_items, dict):
            yield Message(**zero_or_more_items).as_promise
        elif isinstance(zero_or_more_items, str):
            yield Message(zero_or_more_items).as_promise
        elif isinstance(zero_or_more_items, BaseException):
            raise zero_or_more_items
        elif hasattr(zero_or_more_items, "__iter__"):
            for item in zero_or_more_items:
                async for message_promise in self._flattener(item):
                    yield message_promise
        elif hasattr(zero_or_more_items, "__aiter__"):
            async for item in zero_or_more_items:
                async for message_promise in self._flattener(item):
                    yield message_promise
        else:
            raise TypeError(f"Unexpected message type: {type(zero_or_more_items)}")

    async def _resolver(self, seq_promise: MessageSequencePromise) -> tuple[Message, ...]:
        """
        Resolve all the messages in the sequence (which also includes collecting all the streamed tokens)
        and return them as a tuple of Message objects.
        """
        # first collect all the message promises
        msg_promises = [msg_promise async for msg_promise in seq_promise]
        # then resolve them all
        return tuple([await msg_promise for msg_promise in msg_promises])  # pylint: disable=consider-using-generator


# noinspection PyProtectedMember
class AgentReplyMessageSequence(MessageSequence):
    # pylint: disable=protected-access
    """
    TODO Oleksandr: docstring
    """

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
                    if isinstance(self._mini_agent._func_or_class, type):
                        # the miniagent is defined as a class, not as a function -> let's create an instance of this
                        # class and call its `__call__` method
                        actual_func = self._mini_agent._func_or_class(
                            # if we want Pydantic models to also be used as class-based agents, we can't pass
                            # `ctx` as a positional argument (BaseModel's `__init__` doesn't accept positional
                            # arguments unless it is overridden)
                            ctx=ctx,
                            **self._mini_agent._static_kwargs,
                            **self._frozen_kwargs,
                        )
                        await actual_func()
                    else:
                        # the miniagent is a function
                        await self._mini_agent._func_or_class(
                            ctx, **self._mini_agent._static_kwargs, **self._frozen_kwargs
                        )
                finally:
                    await ctx._afinalize()

            return AgentCallNode(  # TODO Oleksandr: why not "persist" this node before the agent function finishes ?
                messages=await self._input_sequence_promise,
                agent=self._mini_agent,
                **dict(self._mini_agent.interaction_metadata),
                # TODO Oleksandr: **self._mini_agent._static_kwargs ?
                **self._frozen_kwargs,
            )

        agent_call_promise = Promise[AgentCallNode](
            start_asap=True,
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
            start_asap=True,  # use a separate async task to avoid deadlock upon AgentReplyNode resolution
            resolver=create_agent_reply_node,
        )


class MessageSequenceAppender(StreamAppender[MessageType]):
    """
    TODO Oleksandr: docstring
    """

    def append(self, piece: MessageType) -> "MessageSequenceAppender":
        super().append(self._freeze_if_possible(piece))
        return self

    @classmethod
    def _freeze_if_possible(cls, zero_or_more_messages: MessageType) -> MessageType:
        if isinstance(zero_or_more_messages, (MessagePromise, Message, str, BaseException)):
            # these types are "frozen enough" as they are
            return zero_or_more_messages
        if isinstance(zero_or_more_messages, BaseModel):
            return Message(**dict(zero_or_more_messages))
        if isinstance(zero_or_more_messages, dict):
            return Message(**zero_or_more_messages)
        if hasattr(zero_or_more_messages, "__iter__"):
            return tuple(cls._freeze_if_possible(item) for item in zero_or_more_messages)
        if hasattr(zero_or_more_messages, "__aiter__"):
            # we do not want to consume an async iterator (and execute its underlying "tasks") prematurely,
            # hence we return it as is
            return zero_or_more_messages

        raise TypeError(f"Unexpected message type: {type(zero_or_more_messages)}")
