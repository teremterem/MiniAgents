# pylint: disable=import-outside-toplevel,cyclic-import
"""
Utility functions of the MiniAgents framework.
"""

import logging
import typing
from typing import AsyncIterator, Any, Optional

# noinspection PyProtectedMember
from pydantic._internal._model_construction import ModelMetaclass

if typing.TYPE_CHECKING:
    from miniagents.messages import Message, MessagePromise
    from miniagents.miniagent_typing import MessageType

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
    messages: "MessageType",
    delimiter: Optional[str] = "\n\n",
    strip_leading_newlines: bool = False,
    reference_original_messages: bool = True,
    start_asap: Optional[bool] = False,
    message_class: Optional[type["Message"]] = None,
    **preliminary_metadata,
) -> "MessagePromise":
    """
    Join multiple messages into a single message using a delimiter.

    :param messages: Messages to join.
    :param delimiter: A string that will be inserted between messages.
    :param strip_leading_newlines: If True, leading newlines will be stripped from each message. Language models,
    when prompted in a certain way, may produce leading newlines in the response. This parameter allows you to
    remove them.
    :param reference_original_messages: If True, the resulting message will contain the list of original messages
    in the `original_messages` field.
    :param start_asap: If True, the resulting message will be scheduled for background resolution regardless
    of when it is going to be consumed.
    :param preliminary_metadata: Metadata that will be available as a field of the resulting MessagePromise even
    before it is resolved.
    :param message_class: A class of the resulting message. If None, the default Message class will be used.
    """
    from miniagents.messages import Message, MESSAGE_CONTENT_AND_TEMPLATE
    from miniagents.miniagents import MessageSequence

    if message_class is None:
        message_class = Message

    async def token_streamer(metadata_so_far: dict[str, Any]) -> AsyncIterator[str]:
        if reference_original_messages:
            metadata_so_far["original_messages"] = []

        first_message = True
        async for message_promise in MessageSequence.turn_into_sequence_promise(messages):
            metadata_so_far.update(message_promise.preliminary_metadata)
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

            # TODO Oleksandr: should I care about merging values of the same keys instead of just overwriting them ?
            metadata_so_far.update(
                (key, value) for key, value in await message_promise if key not in MESSAGE_CONTENT_AND_TEMPLATE
            )

            first_message = False

    return message_class.promise(
        message_token_streamer=token_streamer,
        start_asap=start_asap,
        **preliminary_metadata,
    )
