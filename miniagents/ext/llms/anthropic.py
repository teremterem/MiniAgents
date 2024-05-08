"""
This module integrates Anthropic language models with MiniAgents.
"""

import logging
import typing
from functools import partial
from pprint import pformat
from typing import AsyncIterator, Any, Optional

from miniagents.miniagents import (
    Message,
    miniagent,
    MiniAgent,
    MiniAgents,
    InteractionContext,
)
from miniagents.promising.node import Node

if typing.TYPE_CHECKING:
    import anthropic as anthropic_original

logger = logging.getLogger(__name__)


class AnthropicMessage(Message):
    """
    A message generated by an Anthropic model.
    """

    anthropic: Node


def create_anthropic_agent(
    async_client: Optional["anthropic_original.AsyncAnthropic"] = None,
    assistant_reply_metadata: Optional[dict[str, Any]] = None,
    **mini_agent_kwargs,
) -> MiniAgent:
    """
    Create an MiniAgent for Anthropic models (see MiniAgent class definition and docstring for usage details).
    """
    if not async_client:
        # pylint: disable=import-outside-toplevel
        # noinspection PyShadowingNames
        import anthropic as anthropic_original

        async_client = anthropic_original.AsyncAnthropic()

    return miniagent(
        partial(_anthropic_func, async_client=async_client, global_reply_metadata=assistant_reply_metadata),
        alias="ANTHROPIC_AGENT",
        **mini_agent_kwargs,
    )


async def _anthropic_func(
    ctx: InteractionContext,
    async_client: "anthropic_original.AsyncAnthropic",
    global_reply_metadata: Optional[dict[str, Any]],
    reply_metadata: Optional[dict[str, Any]] = None,
    stream: Optional[bool] = None,
    fake_first_user_message: str = "/start",
    message_delimiter_for_same_role: str = "\n\n",
    **kwargs,
) -> None:
    """
    Run text generation with Anthropic.
    """
    global_reply_metadata = global_reply_metadata or {}
    reply_metadata = reply_metadata or {}
    if stream is None:
        stream = MiniAgents.get_current().stream_llm_tokens_by_default

    async def message_token_producer(metadata_so_far: dict[str, Any]) -> AsyncIterator[str]:
        metadata_so_far.update(global_reply_metadata)
        metadata_so_far.update(reply_metadata)
        collected_messages = await ctx.messages.acollect_messages()

        message_dicts = [_message_to_anthropic_dict(msg) for msg in collected_messages]
        message_dicts = _fix_message_dicts(
            message_dicts,
            fake_first_user_message=fake_first_user_message,
            message_delimiter_for_same_role=message_delimiter_for_same_role,
        )

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("SENDING TO ANTHROPIC:\n\n%s\n", pformat(message_dicts))

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

    ctx.reply(
        AnthropicMessage.promise(
            schedule_immediately=True,  # TODO Oleksandr: should this be customizable ?
            message_token_producer=message_token_producer,
        )
    )


def _message_to_anthropic_dict(message: Message) -> dict[str, Any]:
    # TODO Oleksandr: introduce a lambda function to derive roles from messages ?
    try:
        role = message.role
    except AttributeError:
        try:
            role = message.anthropic_role
        except AttributeError:
            try:
                role = message.anthropic.role
            except AttributeError:
                role = "user"

    return {
        "role": role,
        "content": str(message),
    }


def _fix_message_dicts(
    message_dicts: list[dict[str, Any]], fake_first_user_message: str, message_delimiter_for_same_role: str
) -> list[dict[str, Any]]:
    if not message_dicts:
        return []

    fixed_message_dicts = []
    if message_dicts[0]["role"] != "user":
        # Anthropic requires the first message to come from the user
        fixed_message_dicts.append({"role": "user", "content": fake_first_user_message})

    # if multiple messages with the same role are sent in a row, they should be concatenated
    for message_dict in message_dicts:
        if fixed_message_dicts and message_dict["role"] == fixed_message_dicts[-1]["role"]:
            fixed_message_dicts[-1]["content"] += message_delimiter_for_same_role + message_dict["content"]
        else:
            fixed_message_dicts.append(message_dict)

    return fixed_message_dicts
