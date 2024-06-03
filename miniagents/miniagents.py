"""
"Core" classes of the MiniAgents framework.
"""

import copy
import logging
from functools import partial
from typing import Protocol, AsyncIterator, Any, Union, Optional, Callable, Iterable

from pydantic import BaseModel

from miniagents.messages import MessagePromise, MessageSequencePromise, Message
from miniagents.miniagent_typing import MessageType, AgentFunction
from miniagents.promising.ext.frozen import freeze_dict_values
from miniagents.promising.promise_typing import PromiseStreamer, PromiseBound, PromiseResolvedEventHandler
from miniagents.promising.promising import StreamAppender, Promise, PromisingContext
from miniagents.promising.sentinels import Sentinel, DEFAULT
from miniagents.promising.sequence import FlatSequence

logger = logging.getLogger(__name__)


class PersistMessageEventHandler(Protocol):
    """
    TODO Oleksandr: docstring
    """

    async def __call__(self, promise: PromiseBound, message: Message) -> None: ...


class MiniAgents(PromisingContext):
    """
    TODO Oleksandr: docstring
    """

    def __init__(
        self,
        stream_llm_tokens_by_default: bool = True,
        on_promise_resolved: Union[PromiseResolvedEventHandler, Iterable[PromiseResolvedEventHandler]] = (),
        on_persist_message: Union[PersistMessageEventHandler, Iterable[PersistMessageEventHandler]] = (),
        **kwargs,
    ) -> None:
        on_promise_resolved = (
            [self._trigger_persist_message_event, on_promise_resolved]
            if callable(on_promise_resolved)
            else [self._trigger_persist_message_event, *on_promise_resolved]
        )
        super().__init__(on_promise_resolved=on_promise_resolved, **kwargs)
        self.stream_llm_tokens_by_default = stream_llm_tokens_by_default
        self.on_persist_message_handlers: list[PersistMessageEventHandler] = (
            [on_persist_message] if callable(on_persist_message) else list(on_persist_message)
        )

    @classmethod
    def get_current(cls) -> "MiniAgents":
        """
        TODO Oleksandr: docstring
        """
        # noinspection PyTypeChecker
        return super().get_current()

    def on_persist_message(self, handler: PersistMessageEventHandler) -> PersistMessageEventHandler:
        """
        Add a handler that will be called every time a Message needs to be persisted.
        """
        self.on_persist_message_handlers.append(handler)
        return handler

    # noinspection PyProtectedMember
    async def _trigger_persist_message_event(self, _, obj: Any) -> None:
        """
        TODO Oleksandr: docstring
        """
        # pylint: disable=protected-access
        if not isinstance(obj, Message):
            return

        log_level_for_errors = MiniAgents.get_current().log_level_for_errors

        for sub_message in obj.sub_messages():
            if sub_message._persist_message_event_triggered:
                continue

            for handler in self.on_persist_message_handlers:
                self.start_asap(
                    handler(_, sub_message), suppress_errors=True, log_level_for_errors=log_level_for_errors
                )
            sub_message._persist_message_event_triggered = True

        if obj._persist_message_event_triggered:
            return

        for handler in self.on_persist_message_handlers:
            self.start_asap(handler(_, obj), suppress_errors=True, log_level_for_errors=log_level_for_errors)
        obj._persist_message_event_triggered = True


def miniagent(
    func: Optional[AgentFunction] = None,
    alias: Optional[str] = None,
    description: Optional[str] = None,
    uppercase_func_name: bool = True,
    normalize_spaces_in_docstring: bool = True,
    interaction_metadata: Optional[dict[str, Any]] = None,
    **partial_kwargs,
) -> Union["MiniAgent", Callable[[AgentFunction], "MiniAgent"]]:
    """
    A decorator that converts an agent function into an agent.
    """
    if func is None:
        # the decorator `@miniagent(...)` was used with arguments
        def _decorator(f: AgentFunction) -> "MiniAgent":
            return MiniAgent(
                f,
                alias=alias,
                description=description,
                uppercase_func_name=uppercase_func_name,
                normalize_spaces_in_docstring=normalize_spaces_in_docstring,
                interaction_metadata=interaction_metadata,
                **partial_kwargs,
            )

        return _decorator

    # the decorator `@miniagent` was used either without arguments or as a direct function call
    return MiniAgent(
        func,
        alias=alias,
        description=description,
        uppercase_func_name=uppercase_func_name,
        normalize_spaces_in_docstring=normalize_spaces_in_docstring,
        interaction_metadata=interaction_metadata,
        **partial_kwargs,
    )


class InteractionContext:
    """
    TODO Oleksandr: docstring
    """

    def __init__(
        self, this_agent: "MiniAgent", messages: MessageSequencePromise, reply_streamer: StreamAppender[MessageType]
    ) -> None:
        self.this_agent = this_agent
        self.messages = messages
        self._reply_streamer = reply_streamer

    def reply(self, messages: MessageType) -> None:
        """
        TODO Oleksandr: docstring
        """
        # TODO Oleksandr: add a warning that iterators, async iterators and generators, if passed as `messages` will
        #  not be iterated over immediately, which means that if two agent calls are passed as a generator, those
        #  agent calls will not be scheduled for parallel execution, unless the generator is wrapped into a list (to
        #  guarantee that it will be iterated over immediately)
        # TODO Oleksandr: implement a utility in MiniAgents that deep-copies/freezes mutable data containers
        #  while keeping objects of other types intact and use it in StreamAppender to freeze the state of those
        #  objects upon their submission (this way the user will not have to worry about things like `history[:]`
        #  in the code below)
        self._reply_streamer.append(messages)

    def finish_early(self) -> None:
        """
        TODO Oleksandr: docstring
        TODO Oleksandr: is this a good name for this method ?
        TODO Oleksandr: what to do with exceptions in agent function that may happen after this method was called ?
        """
        self._reply_streamer.close()


class AgentCall:
    """
    TODO Oleksandr: docstring
    TODO Oleksandr: turn this into a context manager ?
    """

    def __init__(
        self,
        message_streamer: StreamAppender[MessageType],
        reply_sequence_promise: MessageSequencePromise,
    ) -> None:
        self._message_streamer = message_streamer
        self._reply_sequence_promise = reply_sequence_promise

        self._message_streamer.open()

    def send_message(self, message: MessageType) -> "AgentCall":
        """
        Send an input message to the agent.
        """
        self._message_streamer.append(message)
        return self

    def reply_sequence(self) -> MessageSequencePromise:
        """
        Finish the agent call and return the agent's response(s).

        NOTE: After this method is called it is not possible to send any more requests to this AgentCall object.
        """
        self.finish()
        return self._reply_sequence_promise

    def finish(self) -> "AgentCall":
        """
        Finish the agent call.

        NOTE: After this method is called it is not possible to send any more requests to this AgentCall object.
        """
        # TODO Oleksandr: also make sure to close the streamer when the parent agent call is finished
        self._message_streamer.close()
        return self


class MiniAgent:
    """
    A wrapper for an agent function that allows calling the agent.
    """

    def __init__(
        self,
        func: AgentFunction,
        alias: Optional[str] = None,
        description: Optional[str] = None,
        # TODO Oleksandr: use DEFAULT for the following two arguments (and put them into MiniAgents class)
        uppercase_func_name: bool = True,
        normalize_spaces_in_docstring: bool = True,
        interaction_metadata: Optional[dict[str, Any]] = None,
        **partial_kwargs,
    ) -> None:
        self._func = func
        if partial_kwargs:
            self._func = partial(func, **partial_kwargs)
        self.frozen_interact_metadata = freeze_dict_values(interaction_metadata or {})  # validate the metadata

        self.alias = alias
        if self.alias is None:
            self.alias = func.__name__
            if uppercase_func_name:
                self.alias = self.alias.upper()

        self.description = description
        if self.description is None:
            self.description = func.__doc__
            if self.description and normalize_spaces_in_docstring:
                self.description = " ".join(self.description.split())
        if self.description:
            # replace all {AGENT_ALIAS} entries in the description with the actual agent alias
            self.description = self.description.format(AGENT_ALIAS=self.alias)

        self.__name__ = self.alias
        self.__doc__ = self.description

    def inquire(
        self,
        messages: Optional[MessageType] = None,
        start_asap: Union[bool, Sentinel] = DEFAULT,
        **function_kwargs,
    ) -> MessageSequencePromise:
        """
        TODO Oleksandr: docstring
        """
        agent_call = self.initiate_inquiry(start_asap=start_asap, **function_kwargs)
        if messages is not None:
            agent_call.send_message(messages)
        return agent_call.reply_sequence()

    def initiate_inquiry(
        self,
        start_asap: Union[bool, Sentinel] = DEFAULT,
        **function_kwargs,
    ) -> "AgentCall":
        """
        TODO Oleksandr: docstring
        """
        input_sequence = MessageSequence(
            start_asap=False,
        )
        reply_sequence = AgentReplyMessageSequence(
            mini_agent=self,
            function_kwargs=function_kwargs,
            input_sequence_promise=input_sequence.sequence_promise,
            start_asap=start_asap,
        )

        agent_call = AgentCall(
            message_streamer=input_sequence.message_appender,
            reply_sequence_promise=reply_sequence.sequence_promise,
        )
        return agent_call


class AgentInteractionNode(Message):
    """
    TODO Oleksandr
    """

    agent_alias: str


class AgentCallNode(AgentInteractionNode):
    """
    TODO Oleksandr
    """

    messages: tuple[Message, ...]


class AgentReplyNode(AgentInteractionNode):
    """
    TODO Oleksandr
    """

    agent_call: AgentCallNode
    replies: tuple[Message, ...]


class MessageSequence(FlatSequence[MessageType, MessagePromise]):
    """
    TODO Oleksandr: produce a docstring for this class after you actually use it in real agents
    """

    message_appender: Optional[StreamAppender[MessageType]]
    sequence_promise: MessageSequencePromise

    def __init__(
        self,
        appender_capture_errors: Union[bool, Sentinel] = DEFAULT,
        start_asap: Union[bool, Sentinel] = DEFAULT,
        incoming_streamer: Optional[PromiseStreamer[MessageType]] = None,
    ) -> None:
        if incoming_streamer:
            # an external streamer is provided, so we don't create the default StreamAppender
            self.message_appender = None
        else:
            self.message_appender = StreamAppender(capture_errors=appender_capture_errors)
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

    @classmethod
    async def aresolve_messages(cls, messages: MessageType) -> tuple[Message, ...]:
        """
        Convert an arbitrarily nested collection of messages of various types (strings, dicts, Message objects,
        MessagePromise objects etc. - see `MessageType` definition for details) into a flat and uniform tuple of
        Message objects.
        """
        return await cls.turn_into_sequence_promise(messages).aresolve_messages()

    async def _flattener(  # pylint: disable=invalid-overridden-method
        self, zero_or_more_items: MessageType
    ) -> AsyncIterator[MessagePromise]:
        if isinstance(zero_or_more_items, MessagePromise):
            yield zero_or_more_items
        elif isinstance(zero_or_more_items, Message):
            yield zero_or_more_items.as_promise
        elif isinstance(zero_or_more_items, BaseModel):
            yield Message(**zero_or_more_items.model_dump()).as_promise
        elif isinstance(zero_or_more_items, dict):
            yield Message(**zero_or_more_items).as_promise
        elif isinstance(zero_or_more_items, str):
            yield Message(text=zero_or_more_items).as_promise
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


class AgentReplyMessageSequence(MessageSequence):
    """
    TODO Oleksandr: docstring
    """

    def __init__(
        self,
        mini_agent: MiniAgent,
        input_sequence_promise: MessageSequencePromise,
        function_kwargs: dict[str, Any],
        **kwargs,
    ) -> None:
        self._frozen_func_kwargs = freeze_dict_values(function_kwargs)  # this validates the agent function kwargs
        self._function_kwargs = copy.deepcopy(function_kwargs)

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
                messages=self._input_sequence_promise,
                reply_streamer=self.message_appender,
            )
            with self.message_appender:
                # errors are not raised above this `with` block, thanks to `appender_capture_errors=True`
                # pylint: disable=protected-access
                # noinspection PyProtectedMember
                await self._mini_agent._func(ctx, **self._function_kwargs)

            return AgentCallNode(
                messages=await self._input_sequence_promise.aresolve_messages(),
                agent_alias=self._mini_agent.alias,
                **self._mini_agent.frozen_interact_metadata,
                # NOTE: the next line will override any keys from `self.interaction_metadata` if names collide
                **self._frozen_func_kwargs,
            )

        agent_call_promise = Promise[AgentCallNode](
            start_asap=True,
            resolver=run_the_agent,
        )

        async for reply_promise in super()._streamer(_):
            yield reply_promise  # at this point all MessageType items are "flattened" into MessagePromise items

        async def create_agent_reply_node(_) -> AgentReplyNode:
            return AgentReplyNode(
                replies=await self.sequence_promise.aresolve_messages(),
                agent_alias=self._mini_agent.alias,
                agent_call=await agent_call_promise,
                **self._mini_agent.frozen_interact_metadata,
            )

        Promise[AgentReplyNode](
            start_asap=True,  # use a separate async task to avoid deadlock upon AgentReplyNode resolution
            resolver=create_agent_reply_node,
        )
