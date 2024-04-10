"""
This module integrates Anthropic language models with MiniAgents.
"""

import typing
from typing import AsyncIterator, Any, Optional, Union

from miniagents.miniagents import MessagePromise, MessageType, MessageSequence, Message
from miniagents.promisegraph.promise import PromiseContext
from miniagents.promisegraph.sentinels import Sentinel, DEFAULT

if typing.TYPE_CHECKING:
    import anthropic as anthropic_original


def anthropic(
    messages: MessageType,
    schedule_immediately: Union[bool, Sentinel] = DEFAULT,
    stream: Union[bool, Sentinel] = DEFAULT,
    async_client: Optional["anthropic_original.AsyncAnthropic"] = None,
    **kwargs,
) -> MessagePromise:
    """
    Run text generation with Anthropic.
    """
    if not async_client:
        # pylint: disable=import-outside-toplevel
        # noinspection PyShadowingNames
        import anthropic as anthropic_original

        # TODO Oleksandr: instantiate the client only once (but still don't import `anthropic` at the module level)
        async_client = anthropic_original.AsyncAnthropic()

    if stream is DEFAULT:
        stream = PromiseContext().stream_llm_tokens_by_default

    async def message_token_producer(metadata_so_far: dict[str, Any]) -> AsyncIterator[str]:
        collected_messages = await MessageSequence.acollect_messages(messages)
        message_dicts = [_message_to_anthropic_dict(msg) for msg in collected_messages]

        metadata_so_far["agent_call"] = {
            "anthropic": {
                "message_hash_keys": tuple(msg.hash_key for msg in collected_messages),
                "stream": stream,
                **kwargs,
            },
        }

        if stream:
            # pylint: disable=not-async-context-manager
            async with async_client.messages.stream(messages=message_dicts, **kwargs) as response:
                async for token in response.text_stream:
                    yield token
                anthropic_final_message = await response.get_final_message()
            # # TODO Oleksandr: if PromptLayer support is needed, but `text_stream` is still not supported by
            # #  PromptLayer, switch back to the version of the code below. Here is a link to the related GitHub
            # #  issue comment:
            # #  - https://github.com/MagnivOrg/prompt-layer-library/issues/126#issuecomment-2040436402
            # response = await async_client.messages.create(messages=message_dicts, stream=True, **kwargs)
            # async for token in response:
            #     if isinstance(token, ContentBlockDeltaEvent):
            #         yield token.delta.text
        else:
            anthropic_final_message = await async_client.messages.create(
                messages=message_dicts, stream=False, **kwargs
            )
            if len(anthropic_final_message.content) != 1:
                raise RuntimeError(
                    f"exactly one TextBlock was expected from Anthropic, "
                    f"but {len(anthropic_final_message.content)} were returned instead"
                )
            yield anthropic_final_message.content[0].text  # yield the whole text as one "piece"

        metadata_so_far["anthropic"] = anthropic_final_message.model_dump(exclude={"content"})

    return MessagePromise(
        message_token_producer=message_token_producer,
        schedule_immediately=schedule_immediately,
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
