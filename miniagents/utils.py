"""
Utility functions of the MiniAgents framework.
"""

import logging
from typing import AsyncIterator, Any, Optional, Union, Iterable, Callable

from miniagents.messages import MessageSequencePromise
from miniagents.miniagents import MessageType, MessageSequence, MessagePromise, Message, MiniAgent
from miniagents.promising.promising import StreamAppender
from miniagents.promising.sentinels import Sentinel, DEFAULT, AWAIT, CLEAR

logger = logging.getLogger(__name__)


async def achain_loop(
    agents: Iterable[Union[MiniAgent, Callable[[MessageType, ...], MessageSequencePromise], Sentinel]],
    initial_input: MessageType = None,
) -> None:
    """
    TODO Oleksandr: docstring
    """
    agents = list(agents)
    if not any(agent is AWAIT for agent in agents):
        raise ValueError(
            "There should be at least one AWAIT sentinel in the list of agents in order for the loop not to "
            "schedule the turns infinitely without actually running them."
        )

    messages = initial_input
    while True:
        for agent in agents:
            if agent is AWAIT:
                if isinstance(messages, MessageSequencePromise):
                    # all the interactions happen here (here all the scheduled promises are awaited for)
                    messages = await messages.acollect_messages()
            elif agent is CLEAR:
                messages = None
            elif callable(agent):
                messages = agent(messages)
            elif isinstance(agent, MiniAgent):
                messages = agent.inquire(messages)
            else:
                raise ValueError(f"Invalid agent: {agent}")
    # TODO Oleksandr: How should agents end the loop ? What message sequence should this utility return when the
    #  loop is over ?


def join_messages(
    messages: MessageType,
    delimiter: Optional[str] = "\n\n",
    strip_leading_newlines: bool = False,
    reference_original_messages: bool = True,
    schedule_immediately: Union[bool, Sentinel] = DEFAULT,
    **message_metadata,
) -> MessagePromise:
    """
    Join multiple messages into a single message using a delimiter.

    :param messages: A list of messages to join.
    :param strip_leading_newlines: If True, leading newlines will be stripped from each message. Language models,
    when prompted in a certain way, may produce leading newlines in the response. This parameter allows you to
    remove them.
    :param delimiter: A string that will be inserted between messages.
    :param reference_original_messages: If True, the resulting message will contain the list of original messages in
    the `original_messages` field.
    :param schedule_immediately: If True, the resulting message will be scheduled for background resolution regardless
    of when it is going to be consumed.
    :param message_metadata: Additional metadata to be added to the resulting message.
    """

    async def token_producer(metadata_so_far: dict[str, Any]) -> AsyncIterator[str]:
        metadata_so_far.update(message_metadata)
        if reference_original_messages:
            metadata_so_far["original_messages"] = []

        first_message = True
        async for message_promise in MessageSequence.turn_into_sequence_promise(messages):
            if delimiter and not first_message:
                yield delimiter

            lstrip_newlines = strip_leading_newlines
            async for token in message_promise:
                if lstrip_newlines:
                    # let's remove leading newlines from the first message
                    token = token.lstrip("\n\r")
                if token:
                    lstrip_newlines = False  # non-empty token was found - time to stop stripping newlines
                    yield token

            if reference_original_messages:
                metadata_so_far["original_messages"].append(await message_promise)

            first_message = False

    return Message.promise(
        message_token_streamer=token_producer,
        schedule_immediately=schedule_immediately,
    )


def split_messages(
    messages: MessageType,
    delimiter: str = "\n\n",
    code_block_delimiter: Optional[str] = "```",
    schedule_immediately: Union[bool, Sentinel] = DEFAULT,
    **message_metadata,
) -> MessageSequencePromise:
    """
    TODO Oleksandr: docstring
    """

    # pylint: disable=not-context-manager,too-many-statements

    # TODO Oleksandr: convert this function into a class ?
    # TODO Oleksandr: simplify this function somehow ? it is not going to be easy to understand later
    # TODO Oleksandr: but cover it with unit tests first
    async def sequence_producer(_) -> AsyncIterator[MessagePromise]:
        text_so_far = ""
        current_text_producer: Optional[StreamAppender[str]] = None
        inside_code_block = False

        def is_text_so_far_not_empty() -> bool:
            return bool(text_so_far.replace(delimiter, ""))

        def split_text_if_needed() -> bool:
            nonlocal text_so_far, current_text_producer, inside_code_block

            delimiter_idx = -1 if inside_code_block else text_so_far.find(delimiter)
            delimiter_len = len(delimiter)

            code_delimiter_idx = text_so_far.find(
                code_block_delimiter,
                len(code_block_delimiter) if inside_code_block else 0,  # skip the opening delimiter if we're inside
            )
            if code_delimiter_idx > -1 and (delimiter_idx < 0 or code_delimiter_idx < delimiter_idx):
                delimiter_len = 0  # we want to include the code block delimiters into the text of the code message
                if inside_code_block:
                    delimiter_idx = code_delimiter_idx + len(code_block_delimiter)
                else:
                    delimiter_idx = code_delimiter_idx
                inside_code_block = not inside_code_block

            if delimiter_idx < 0:
                return False

            text = text_so_far[:delimiter_idx]
            text_so_far = text_so_far[delimiter_idx + delimiter_len :]
            if text:
                with current_text_producer:
                    current_text_producer.append(text)
                current_text_producer = None
            return True

        def start_new_message_promise() -> MessagePromise:
            nonlocal current_text_producer
            current_text_producer = StreamAppender[str]()

            async def token_producer(metadata_so_far: dict[str, Any]) -> AsyncIterator[str]:
                metadata_so_far.update(message_metadata)
                async for token in current_text_producer:
                    yield token

            return Message.promise(
                message_token_streamer=token_producer,
                schedule_immediately=schedule_immediately,
            )

        try:
            if not current_text_producer:
                # we already know that there will be at least one message - time to make a promise
                yield start_new_message_promise()

            async for token in join_messages(
                messages,
                delimiter=delimiter,
                reference_original_messages=False,
                schedule_immediately=schedule_immediately,
            ):
                text_so_far += token

                while True:
                    # TODO Oleksandr: this loop doesn't really work when we are not in streaming mode (when the whole
                    #  message is available at once) - only the first and the last paragraph is returned, middle
                    #  paragraphs are lost
                    if not current_text_producer and is_text_so_far_not_empty():
                        # previous message was already sent - we need to start a new one (make a new promise)
                        yield start_new_message_promise()
                    if not split_text_if_needed():
                        # repeat splitting until no more splitting is happening anymore in the text that we have so far
                        break

            if is_text_so_far_not_empty():
                # some text still remains after all the messages have been processed
                if current_text_producer:
                    with current_text_producer:
                        current_text_producer.append(text_so_far)
                else:
                    yield Message(text=text_so_far, **message_metadata).as_promise

        except BaseException as exc:  # pylint: disable=broad-except
            logger.debug("Error while processing a message sequence inside `split_messages`", exc_info=True)
            if current_text_producer:
                with current_text_producer:
                    # noinspection PyTypeChecker
                    current_text_producer.append(exc)  # TODO Oleksandr: update StreamAppender's signature ?
            else:
                raise exc
        finally:
            if current_text_producer:
                # in case of an exception and the last MessagePromise "still hanging"
                current_text_producer.close()

    async def sequence_packager(sequence_promise: MessageSequencePromise) -> tuple[MessagePromise, ...]:
        return tuple([item async for item in sequence_promise])  # pylint: disable=consider-using-generator

    return MessageSequencePromise(
        producer=sequence_producer,
        packager=sequence_packager,
        schedule_immediately=True,  # allowing it to ever be False results in a deadlock
    )
