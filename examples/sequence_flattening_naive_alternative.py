"""
Naive Async Generator Alternative to Sequence Flattening

This example provides a contrast to `sequence_flattening.py`. It replicates the
same sequence of actions but uses Python's vanila async generators and no
MiniAgents framework.

The main difference is that the `async for ... yield` constructs process the
generators sequentially. The `web_search_agent_naive` for "query 2" will only
start after the one for "query 1" (including all its pretend-scraping)
is finished.

Secondly, message sequence replayability is not supported. Once a generator is
consumed, it's exhausted.
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
    yield f"{search_query} - SEARCH DONE"

    for i in range(2):
        url = f"https://dummy.com/{search_query.replace(' ', '-')}/page-{i+1}"
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
    print("=== Naive Async Generator Execution ===")
    print()

    # Consume and print results sequentially
    await stream_to_stdout_naive(result_generator)

    print()
    print("=== End of Naive Execution ===")
    print()

    print("Attempting to reiterate (WILL YIELD NOTHING):")
    # await asyncio.sleep(0.2)

    # NOTE: Re-iterating a standard async generator like this is not possible.
    # Once consumed, it's exhausted. This contrasts with MiniAgents promises,
    # which are replayable.
    await stream_to_stdout_naive(result_generator)  # This won't print anything

    print("=== End of Reiteration Attempt ===")
    print()


if __name__ == "__main__":
    asyncio.run(main_naive())
