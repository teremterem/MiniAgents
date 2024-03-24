"""
This module integrates Anthropic language models with PromiseGraph / MiniAgents.
"""

from typing import AsyncIterator, Any

from promisegraph.miniagents.miniagents import MessagePromise


def anthropic(schedule_immediately: bool = True, stream: bool = True, **kwargs) -> MessagePromise:
    """
    Run text generation with Anthropic.
    """
    # pylint: disable=import-outside-toplevel
    import anthropic as anthropic_original
    from anthropic.types import ContentBlockDeltaEvent

    # TODO Oleksandr: instantiate the client only once but don't import `anthropic` at the module level
    client = anthropic_original.AsyncAnthropic()

    async def msg_piece_producer(_: dict[str, Any]) -> AsyncIterator[str]:
        response = await client.messages.create(stream=stream, **kwargs)
        # TODO Oleksandr: collect metadata_so_far
        if stream:
            async for token in response:
                if isinstance(token, ContentBlockDeltaEvent):
                    yield token.delta.text
        else:
            if len(response.content) != 1:
                raise RuntimeError(
                    f"exactly one message should have been returned by Anthropic, "
                    f"but {len(response.content)} were returned instead"
                )
            yield response.content[0].text

    return MessagePromise(msg_piece_producer=msg_piece_producer, schedule_immediately=schedule_immediately)
