"""
Utility functions of the MiniAgents framework.
"""

from typing import AsyncIterator, Any, Optional

from miniagents.miniagents import MessageType, MessageSequence, MessagePromise, Message


def join_messages(
    messages: MessageType,
    delimiter: Optional[str] = "\n\n",
    strip_leading_newlines: bool = False,
    collect_original_message_hash_keys: bool = True,
    **message_metadata,
) -> MessagePromise:
    """
    Join multiple messages into a single message using a delimiter.

    :param messages: A list of messages to join.
    :param strip_leading_newlines: If True, leading newlines will be stripped from each message. Language models,
    when prompted in a certain way, may produce leading newlines in the response. This parameter allows you to
    remove them.
    :param delimiter: A string that will be inserted between messages.
    :param collect_original_message_hash_keys: If True, the hash keys of the original messages will be collected
    and stored in the metadata of the resulting message (`original_message_hash_keys` field).
    :param message_metadata: Additional metadata to be added to the resulting message.
    """

    async def token_producer(metadata_so_far: dict[str, Any]) -> AsyncIterator[str]:
        if collect_original_message_hash_keys:
            metadata_so_far["original_message_hash_keys"] = []
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

            if collect_original_message_hash_keys:
                metadata_so_far["original_message_hash_keys"].append((await message_promise.acollect()).hash_key)

            first_message = False

        metadata_so_far.update(message_metadata)

    return Message.promise(message_token_producer=token_producer)
