"""
Utility functions of the MiniAgents framework.
"""

import logging
from typing import AsyncIterator, Any, Optional

# noinspection PyProtectedMember
from pydantic._internal._model_construction import ModelMetaclass

from miniagents.miniagents import MessageType, MessageSequence, MessagePromise, Message

logger = logging.getLogger(__name__)


class SingletonMeta(type):
    """
    A metaclass that ensures that only one instance of a certain class is created.
    NOTE: This metaclass is designed to work in asynchronous environments, hence we didn't bother making
    it thread-safe (people typically don't mix multithreading and asynchronous paradigms together).
    """

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


def join_messages(
    messages: MessageType,
    delimiter: Optional[str] = "\n\n",
    strip_leading_newlines: bool = False,
    reference_original_messages: bool = True,
    start_asap: Optional[bool] = False,
    **message_metadata,
) -> MessagePromise:
    """
    Join multiple messages into a single message using a delimiter.

    :param messages: Messages to join.
    :param delimiter: A string that will be inserted between messages.
    :param strip_leading_newlines: If True, leading newlines will be stripped from each message. Language models,
    when prompted in a certain way, may produce leading newlines in the response. This parameter allows you to
    remove them.
    :param reference_original_messages: If True, the resulting message will contain the list of original messages in
    the `original_messages` field.
    :param start_asap: If True, the resulting message will be scheduled for background resolution regardless
    of when it is going to be consumed.
    :param message_metadata: Additional metadata to be added to the resulting message.
    """

    async def token_streamer(metadata_so_far: dict[str, Any]) -> AsyncIterator[str]:
        metadata_so_far.update(message_metadata)
        if reference_original_messages:
            metadata_so_far["original_messages"] = []

        first_message = True
        async for message_promise in MessageSequence.turn_into_sequence_promise(messages):
            # TODO Oleksandr: accumulate metadata from all the messages !!!
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
        message_token_streamer=token_streamer,
        start_asap=start_asap,
    )
