"""
Naive Async Generator Alternative to Sequence Flattening

This example provides a contrast to `sequence_flattening.py`. It attempts
to mimic the structure using standard Python `async def`, `yield`, and `yield from`
without the MiniAgents framework.

Crucially, this naive implementation using `yield from` results in **sequential**
execution of the sub-generators. It does not automatically achieve the concurrency
and background processing that MiniAgents provides with sequence flattening.
This difference highlights the complexity MiniAgents handles automatically.

To achieve concurrency similar to the MiniAgents example, one would need to
manually manage tasks using `asyncio.create_task` and potentially queues or
other synchronization primitives to yield results as they become available,
significantly increasing complexity.
"""

import asyncio
import random
from typing import AsyncGenerator


async def research_agent_naive(question: str) -> AsyncGenerator[str, None]:
    """
    The main research agent, implemented naively.
    Calls web_search_agent_naive sequentially using a `yield from` analogue -
    `async for ... yield` (`yield from` does not work with async generators).
    """
    yield f"RESEARCHING: {question}"

    for i in range(3):
        query = f"query {i+1}"
        # NOTE: The `async for ... yield` construct processes the generator
        # sequentially. The `web_search_agent_naive` for "query 2" will only
        # start after the one for "query 1" (including all its pretend-scraping)
        # is finished.
        async for item in web_search_agent_naive(search_query=query):
            yield item


async def web_search_agent_naive(search_query: str) -> AsyncGenerator[str, None]:
    """
    Pretends to perform a web search and trigger scraping.
    Calls page_scraper_agent_naive sequentially using a `yield from` analogue -
    `async for ... yield`.
    """
    yield f"{search_query} - SEARCHING"
    await asyncio.sleep(random.uniform(0.5, 1))
    yield f"{search_query} - DONE"

    for i in range(3):
        url = f"http://dummy.page/{search_query.replace(' ', '-')}/page-{i+1}"
        # NOTE: The `async for ... yield` construct leads to sequential execution.
        # The next iteration or yield in this function only happens *after*
        # page_scraper_agent_naive is completely finished.
        async for item in page_scraper_agent_naive(url=url):
            yield item


async def page_scraper_agent_naive(url: str) -> AsyncGenerator[str, None]:
    """
    Pretends to scrape a web page.
    Yields simple status messages.
    """
    yield f"{url} - SCRAPING"
    await asyncio.sleep(random.uniform(0.5, 1))
    yield f"{url} - DONE"


async def stream_to_stdout_naive(generator: AsyncGenerator[str, None]):
    """
    Consumes the async generator and prints yielded strings.
    """
    i = 0
    async for message in generator:
        i += 1
        print(f"String {i}: {message}")


async def main_naive():
    """
    Main function to trigger the naive research agent and print the results.
    """
    question = "Tell me about MiniAgents sequence flattening (naive version)"
    # Get the async generator
    result_generator = research_agent_naive(question)

    print()
    print("--- Naive Async Generator Execution ---")
    print()
    # Consume and print results sequentially
    await stream_to_stdout_naive(result_generator)
    print()
    print("--- End of Naive Execution ---")
    print()

    print()
    print("Attempting to reiterate (will yield nothing):")
    # Note: Re-iterating a standard async generator like this is not possible.
    # Once consumed, it's exhausted. This contrasts with MiniAgents promises,
    # which are replayable.
    await stream_to_stdout_naive(result_generator)  # This won't print anything
    print("--- End of Reiteration Attempt ---")
    print()


if __name__ == "__main__":
    asyncio.run(main_naive())
