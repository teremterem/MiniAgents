# pylint: disable=too-many-arguments
"""
Split this module into multiple modules.
"""

from typing import Protocol, AsyncIterator, Any, Union, Iterable, AsyncIterable, Optional, Callable

from miniagents.promisegraph.node import Node
from miniagents.promisegraph.promise import StreamedPromise, AppendProducer, Promise
from miniagents.promisegraph.sentinels import Sentinel, DEFAULT
from miniagents.promisegraph.sequence import FlatSequence


class Message(Node):
    """
    A message that can be sent between agents.
    """

    text: str


class AgentCallNode(Node):
    """
    TODO TODO TODO Oleksandr
    """

    message_hash_keys: tuple[str, ...]


class MessageTokenProducer(Protocol):
    """
    A protocol for message piece producer functions.
    """

    def __call__(self, metadata_so_far: dict[str, Any]) -> AsyncIterator[str]: ...


class MessagePromise(StreamedPromise[str, Message]):
    """
    A promise of a message that can be streamed token by token.
    """

    def __init__(
        self,
        schedule_immediately: Union[bool, Sentinel] = DEFAULT,
        message_token_producer: MessageTokenProducer = None,
        prefill_message: Optional[Message] = None,
        metadata_so_far: Optional[Node] = None,
    ) -> None:
        # TODO Oleksandr: raise an error if both ready_message and message_token_producer/metadata_so_far are not None
        #  (or both are None)
        if prefill_message:
            super().__init__(
                schedule_immediately=schedule_immediately,
                prefill_pieces=[prefill_message.text],
                prefill_whole=prefill_message,
            )
        else:
            super().__init__(
                schedule_immediately=schedule_immediately,
                producer=self._producer,
                packager=self._packager,
            )
            self._message_token_producer = message_token_producer
            self._metadata_so_far: dict[str, Any] = metadata_so_far.model_dump() if metadata_so_far else {}

    def _producer(self, _) -> AsyncIterator[str]:
        return self._message_token_producer(self._metadata_so_far)

    async def _packager(self, _) -> Message:
        return Message(
            text="".join([token async for token in self]),
            **self._metadata_so_far,
        )

    def __aiter__(self) -> AsyncIterator[str]:
        # PyCharm fails to see that MessagePromise inherits AsyncIterable protocol from StreamedPromise,
        # hence the need to explicitly declare the __aiter__ method here
        return super().__aiter__()


# TODO Oleksandr: add documentation somewhere that explains what MessageType and SingleMessageType represent
SingleMessageType = Union[str, dict[str, Any], Message, MessagePromise, BaseException]
MessageType = Union[SingleMessageType, Iterable["MessageType"], AsyncIterable["MessageType"]]


class MessageSequencePromise(StreamedPromise[MessagePromise, tuple[MessagePromise, ...]]):
    """
    A promise of a sequence of messages that can be streamed message by message.
    """

    async def acollect_messages(self) -> tuple[Message, ...]:
        """
        Collect all messages from the sequence and return them as a tuple of Message objects.
        """
        # pylint: disable=consider-using-generator
        return tuple([await message_promise.acollect() async for message_promise in self])

    def __aiter__(self) -> AsyncIterator[MessagePromise]:
        # PyCharm fails to see that MessageSequencePromise inherits AsyncIterable protocol from StreamedPromise,
        # hence the need to explicitly declare the __aiter__ method here
        return super().__aiter__()


class MessageSequence(FlatSequence[MessageType, MessagePromise]):
    """
    TODO Oleksandr: produce a docstring for this class after you actually use it in real agents
    """

    sequence_promise: MessageSequencePromise

    def __init__(
        self,
        producer_capture_errors: Union[bool, Sentinel] = DEFAULT,
        schedule_immediately: Union[bool, Sentinel] = DEFAULT,
    ) -> None:
        super().__init__(
            flattener=self._flattener,
            schedule_immediately=schedule_immediately,
            producer_capture_errors=producer_capture_errors,
            sequence_promise_class=MessageSequencePromise,
        )

    @classmethod
    async def acollect_messages(cls, messages: MessageType) -> tuple[Message, ...]:
        """
        Convert an arbitrarily nested collection of messages of various types (strings, dicts, Message objects,
        MessagePromise objects etc. - see `MessageType` definition for details) into a flat and uniform tuple of
        Message objects.
        """
        message_sequence = cls(
            producer_capture_errors=True,
            schedule_immediately=False,
        )
        with message_sequence.append_producer:
            message_sequence.append_producer.append(messages)
        return await message_sequence.sequence_promise.acollect_messages()

    @staticmethod
    async def _flattener(_, zero_or_more_items: MessageType) -> AsyncIterator[MessagePromise]:
        if isinstance(zero_or_more_items, MessagePromise):
            yield zero_or_more_items
        elif isinstance(zero_or_more_items, Message):
            yield MessagePromise(prefill_message=zero_or_more_items)
        elif isinstance(zero_or_more_items, str):
            yield MessagePromise(prefill_message=Message(text=zero_or_more_items))
        elif isinstance(zero_or_more_items, dict):
            yield MessagePromise(prefill_message=Message(**zero_or_more_items))
        elif isinstance(zero_or_more_items, BaseException):
            raise zero_or_more_items
        elif hasattr(zero_or_more_items, "__iter__"):
            for item in zero_or_more_items:
                async for message_promise in MessageSequence._flattener(_, item):
                    yield message_promise
        elif hasattr(zero_or_more_items, "__aiter__"):
            async for item in zero_or_more_items:
                async for message_promise in MessageSequence._flattener(_, item):
                    yield message_promise
        else:
            raise TypeError(f"unexpected message type: {type(zero_or_more_items)}")


class AgentFunction(Protocol):
    """
    A protocol for agent functions.
    """

    def __call__(self, messages: MessageSequencePromise, **kwargs) -> AsyncIterator[MessageType]: ...


class MiniAgent:
    """
    A wrapper for an agent function that allows calling the agent.
    """

    def __init__(
        self,
        func: AgentFunction,
        alias: Optional[str] = None,
        description: Optional[str] = None,
        uppercase_func_name: bool = True,
        normalize_spaces_in_docstring: bool = True,
    ) -> None:
        self._func = func

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
        schedule_immediately: Union[bool, Sentinel] = DEFAULT,
        **function_kwargs,
    ) -> MessageSequencePromise:
        """
        TODO TODO TODO Oleksandr: update this docstring
        "Ask" the agent and immediately receive an AsyncMessageSequence object that can be used to obtain the agent's
        response(s). If blank_history is False and history_tracker/branch_from is not specified and pre-existing
        messages are passed as requests (for ex. messages that came from other agents), then this agent call will be
        automatically branched off of the conversation branch those pre-existing messages belong to (the history will
        be inherited from those messages, in other words).
        """
        agent_call = self.initiate_inquiry(schedule_immediately=schedule_immediately, **function_kwargs)
        if messages is not None:
            agent_call.send_message(messages)
        return agent_call.reply_sequence()

    def initiate_inquiry(
        self,
        schedule_immediately: Union[bool, Sentinel] = DEFAULT,
        **function_kwargs,
    ) -> "AgentCall":
        """
        TODO TODO TODO Oleksandr: update this docstring
        Initiate the process of "asking" the agent. Returns an AgentCall object that can be used to send requests to
        the agent by calling `send_request()` zero or more times and receive its responses by calling
        `response_sequence()` at the end. If blank_history is False and history_tracker/branch_from is not specified
        and pre-existing messages are passed as requests (for ex. messages that came from other agents), then this
        agent call will be automatically branched off of the conversation branch those pre-existing messages belong to
        (the history will be inherited from those messages, in other words).
        """
        message_sequence = MessageSequence(
            producer_capture_errors=False,  # TODO TODO TODO Oleksandr: is this the right value ?
            schedule_immediately=schedule_immediately,
        )
        reply_sequence = MessageSequence(
            producer_capture_errors=False,  # TODO TODO TODO Oleksandr: is this the right value ?
            schedule_immediately=schedule_immediately,
        )
        agent_call = AgentCall(
            message_producer=message_sequence.append_producer,
            reply_sequence_promise=reply_sequence.sequence_promise,
        )

        async def _agent_call_fulfiller(_) -> AgentCallNode:
            with reply_sequence.append_producer:
                async for reply in self._func(message_sequence.sequence_promise, **function_kwargs):
                    reply_sequence.append_producer.append(reply)
            message_hash_keys = [
                message.hash_key for message in await message_sequence.sequence_promise.acollect_messages()
            ]
            return AgentCallNode(message_hash_keys=message_hash_keys, **function_kwargs)

        # TODO TODO TODO Oleksandr: should I, instead of this promise, override the `message_sequence` producer ?
        #  with current implementation, `schedule_immediately` is probably not respected
        Promise[AgentCallNode](
            schedule_immediately=True,  # TODO TODO TODO Oleksandr: is this the right value ?
            fulfiller=_agent_call_fulfiller,
        )
        return agent_call


def miniagent(
    func: Optional[AgentFunction] = None,
    /,  # TODO Oleksandr: do I really need to enforce positional-only upon `func` ?
    alias: Optional[str] = None,
    description: Optional[str] = None,
    uppercase_func_name: bool = True,
    normalize_spaces_in_docstring: bool = True,
) -> Union["MiniAgent", Callable[[AgentFunction], MiniAgent]]:
    """
    A decorator that converts an agent function into an agent.
    """
    if func is None:
        # the decorator `@miniagent(...)` was used with arguments
        def _decorator(f: "AgentFunction") -> "MiniAgent":
            return MiniAgent(
                f,
                alias=alias,
                description=description,
                uppercase_func_name=uppercase_func_name,
                normalize_spaces_in_docstring=normalize_spaces_in_docstring,
            )

        return _decorator

    # the decorator `@miniagent` was used either without arguments or as a direct function call
    return MiniAgent(
        func,
        alias=alias,
        description=description,
        uppercase_func_name=uppercase_func_name,
        normalize_spaces_in_docstring=normalize_spaces_in_docstring,
    )


class AgentCall:
    """
    TODO TODO TODO Oleksandr: update this docstring
    TODO TODO TODO Oleksandr: turn this into a context manager ?
    A call to an agent. This object is returned by Agent.start_asking()/start_telling() methods. It is used to send
    requests to the agent and receive its responses.
    """

    def __init__(
        self,
        message_producer: AppendProducer[MessageType],
        reply_sequence_promise: MessageSequencePromise,
    ) -> None:
        self._message_producer = message_producer
        self._reply_sequence_promise = reply_sequence_promise

        self._message_producer.open()

    def send_message(self, message: MessageType) -> "AgentCall":
        """
        TODO TODO TODO Oleksandr: update this docstring ?
        Send a request to the agent.
        """
        self._message_producer.append(message)
        return self

    def reply_sequence(self) -> MessageSequencePromise:
        """
        TODO TODO TODO Oleksandr: update this docstring ?
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
        # TODO TODO TODO Oleksandr: also make sure to close the producer when the parent agent call is finished
        self._message_producer.close()
        return self
