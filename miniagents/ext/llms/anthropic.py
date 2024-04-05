"""
This module integrates Anthropic language models with MiniAgents.
"""

import typing
from typing import AsyncIterator, Any, Optional

from anthropic.types import ContentBlockDeltaEvent

from miniagents.miniagents import MessagePromise, MessageType, MessageSequence, Message

if typing.TYPE_CHECKING:
    import anthropic as anthropic_original


def anthropic(
    messages: MessageType,
    schedule_immediately: bool = True,
    collect_as_soon_as_possible: bool = True,
    stream: bool = True,
    async_client: Optional["anthropic_original.AsyncAnthropic"] = None,
    **kwargs,
) -> MessagePromise:
    """
    Run text generation with Anthropic.
    """
    if not async_client:
        # pylint: disable=import-outside-toplevel
        import anthropic as anthropic_original

        # TODO Oleksandr: instantiate the client only once (but still don't import `anthropic` at the module level)
        async_client = anthropic_original.AsyncAnthropic()

    async def message_piece_producer(_: dict[str, Any]) -> AsyncIterator[str]:
        # TODO Oleksandr: collect metadata_so_far
        collected_messages = await MessageSequence.aflatten_and_collect(messages)
        message_dicts = [_message_to_anthropic_dict(msg) for msg in collected_messages]

        if stream:
            response = await async_client.messages.create(messages=message_dicts, stream=True, **kwargs)
            async for token in response:
                if isinstance(token, ContentBlockDeltaEvent):
                    yield token.delta.text
            # # TODO Oleksandr: switch back to the version below when PromptLayer supports `text_stream`
            # # pylint: disable=not-async-context-manager
            # async with async_client.messages.stream(messages=message_dicts, **kwargs) as response:
            #     async for token in response.text_stream:
            #         yield token
        else:
            response = await async_client.messages.create(messages=message_dicts, stream=False, **kwargs)
            if len(response.content) != 1:
                raise RuntimeError(
                    f"exactly one message should have been returned by Anthropic, "
                    f"but {len(response.content)} were returned instead"
                )
            yield response.content[0].text  # yield the whole text as one "piece"

    return MessagePromise(
        message_piece_producer=message_piece_producer,
        schedule_immediately=schedule_immediately,
        collect_as_soon_as_possible=collect_as_soon_as_possible,
    )


def _message_to_anthropic_dict(message: Message) -> dict[str, Any]:
    # TODO Oleksandr: introduce a lambda function to derive roles from messages ?
    try:
        role = message.role
    except AttributeError:
        role = getattr(message, "anthropic_role", "user")

    return {
        "role": role,
        "content": message.text,
    }
