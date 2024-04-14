"""
This module integrates Anthropic language models with MiniAgents.
"""

import typing
from functools import partial
from typing import AsyncIterator, Any, Optional

from miniagents.miniagents import MessagePromise, MessageType, Message, miniagent, MiniAgent, MessageSequencePromise
from miniagents.promisegraph.promise import PromiseContext

if typing.TYPE_CHECKING:
    import anthropic as anthropic_original


def create_anthropic_agent(async_client: Optional["anthropic_original.AsyncAnthropic"] = None) -> MiniAgent:
    """
    Create an MiniAgent for Anthropic models (see MiniAgent class definition and docstring for usage details).
    """
    if not async_client:
        # pylint: disable=import-outside-toplevel
        # noinspection PyShadowingNames
        import anthropic as anthropic_original

        async_client = anthropic_original.AsyncAnthropic()

    return miniagent(partial(_anthropic_func, async_client=async_client), alias="ANTHROPIC_AGENT")


async def _anthropic_func(
    messages: MessageSequencePromise,
    async_client: "anthropic_original.AsyncAnthropic",
    stream: Optional[bool] = None,
    **kwargs,
) -> AsyncIterator[MessageType]:
    """
    Run text generation with Anthropic.
    """
    if stream is None:
        stream = PromiseContext().stream_llm_tokens_by_default

    async def message_token_producer(metadata_so_far: dict[str, Any]) -> AsyncIterator[str]:
        collected_messages = await messages.acollect_messages()
        message_dicts = [_message_to_anthropic_dict(msg) for msg in collected_messages]

        # TODO TODO TODO Oleksandr: leverage AgentCallNode somehow instead of this
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

    yield MessagePromise(
        schedule_immediately=True,  # TODO TODO TODO Oleksandr: is this the right value
        message_token_producer=message_token_producer,
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
