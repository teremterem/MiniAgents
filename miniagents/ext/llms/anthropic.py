"""
This module integrates Anthropic language models with MiniAgents.
"""

from typing import AsyncIterator, Any

from miniagents.miniagents import MessagePromise


def anthropic(
    schedule_immediately: bool = True, collect_as_soon_as_possible: bool = True, stream: bool = True, **kwargs
) -> MessagePromise:
    """
    Run text generation with Anthropic.
    """
    # pylint: disable=import-outside-toplevel
    import anthropic as anthropic_original

    # TODO Oleksandr: instantiate the client only once (but still don't import `anthropic` at the module level)
    client = anthropic_original.AsyncAnthropic()

    async def message_piece_producer(_: dict[str, Any]) -> AsyncIterator[str]:
        # TODO Oleksandr: collect metadata_so_far
        if stream:
            async with client.messages.stream(**kwargs) as response:  # pylint: disable=not-async-context-manager
                async for token in response.text_stream:
                    yield token
        else:
            response = await client.messages.create(stream=False, **kwargs)
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
