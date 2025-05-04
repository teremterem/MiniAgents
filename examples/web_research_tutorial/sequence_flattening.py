import asyncio
import random

from miniagents import InteractionContext, Message, MiniAgents, miniagent, MessageSequencePromise


@miniagent
async def research_agent(ctx: InteractionContext) -> None:
    """
    The main research agent.
    It receives the initial request (a dummy question in this example).
    It breaks the request down into dummy "search queries".
    For each search query, it triggers the web_search_agent.
    Crucially, it collects the results (which are MessageSequencePromise objects)
    from the web_search_agent and includes them directly in its own reply sequence.
    """
    user_question = await ctx.message_promises.as_single_text_promise()
    ctx.reply(f"RESEARCHING: {user_question}")

    # Simulate breaking down the question into 3 dummy search queries
    dummy_search_queries = [f"Dummy Search {i+1} for '{user_question}'" for i in range(3)]

    ctx.reply(f"GENERATED {len(dummy_search_queries)} DUMMY SEARCH QUERIES.")

    # We will collect the promises returned by web_search_agent calls here.
    # Each element added will be a MessageSequencePromise itself.
    all_search_results_promises = []

    for i, search_query in enumerate(dummy_search_queries):
        # Trigger the web_search_agent for each query.
        # IMPORTANT: No `await` here! `trigger` returns immediately with a
        # `MessageSequencePromise`. The actual execution of `web_search_agent`
        # will start in the background when asyncio gets a chance to switch tasks.
        search_results_promise = web_search_agent.trigger(
            # We pass the original user question and the specific search query
            # as context to the web_search_agent.
            [ctx.message_promises, f"SEARCH CONTEXT {i+1}"],
            search_query=search_query,
        )
        # Add the promise for the sequence of results from this specific
        # search_agent call to our list.
        all_search_results_promises.append(search_results_promise)

    # Reply with a sequence that *includes* the collected promises.
    # This is where the "sequence flattening" happens implicitly.
    # `ctx.reply()` accepts lists (or other iterables) of items. These items can be:
    #   - Concrete messages (like strings or Message objects)
    #   - Promises of individual messages (MessagePromise)
    #   - Promises of sequences of messages (MessageSequencePromise) - like we have here!
    # MiniAgents automatically resolves and flattens this nested structure in the
    # background. The consumer of `research_agent`'s response sequence (in this
    # case, the `main` function) will receive a single, flat sequence of messages
    # as if all the messages from the nested sequences were yielded directly by
    # `research_agent`.
    ctx.reply(
        [
            "--- START OF FLATTENED SEARCH RESULTS ---",
            # This list contains MessageSequencePromise objects.
            all_search_results_promises,
            "--- END OF FLATTENED SEARCH RESULTS ---",
        ]
    )


@miniagent
async def web_search_agent(
    ctx: InteractionContext,
    search_query: str,
) -> None:
    """
    Simulates performing a web search for a given query and identifying pages to scrape.
    It receives a search query.
    It generates dummy "page URLs" based on the query.
    For each dummy page URL, it triggers the page_scraper_agent.
    It collects the results (MessageSequencePromise objects) from the page_scraper_agent
    and includes them in its own reply sequence, demonstrating nested flattening.
    """
    ctx.reply(f'SEARCHING FOR: "{search_query}"')

    # Simulate finding 3 dummy pages for the search query
    dummy_pages_to_scrape = [f"http://dummy.page/{search_query.replace(' ', '-')}/page{i+1}" for i in range(3)]

    ctx.reply(f"FOUND {len(dummy_pages_to_scrape)} DUMMY PAGES for '{search_query}'.")

    # We will collect the promises returned by page_scraper_agent calls here.
    # Each element will be a MessageSequencePromise.
    all_scraping_results_promises = []

    for page_url in dummy_pages_to_scrape:
        # Trigger the page_scraper_agent for each dummy URL.
        # Again, no `await`. `trigger` returns a MessageSequencePromise immediately.
        scraping_results_promise = page_scraper_agent.trigger(
            # Pass context to the scraper agent.
            [ctx.message_promises, f"SCRAPE CONTEXT for {page_url}"],
            url=page_url,
        )
        # Add the promise to our list.
        all_scraping_results_promises.append(scraping_results_promise)

    # Reply with a sequence that includes the collected promises from page_scraper_agent.
    # This demonstrates nested sequence flattening. The results from page_scraper_agent
    # will be flattened into the sequence returned by web_search_agent, which in turn
    # gets flattened into the sequence returned by research_agent.
    ctx.reply(
        [
            f"--- Start scraping results for '{search_query}' ---",
            # This list contains MessageSequencePromise objects.
            all_scraping_results_promises,
            f"--- End scraping results for '{search_query}' ---",
        ]
    )


@miniagent
async def page_scraper_agent(
    ctx: InteractionContext,
    url: str,
) -> None:
    """
    Simulates scraping a web page and extracting information.
    It receives a URL.
    It generates a dummy "summary" for the page.
    It replies with simple status messages and the dummy summary.
    This is the innermost agent in this example. Its replies will be flattened
    into web_search_agent's sequence, and then into research_agent's sequence.
    """
    ctx.reply(f"SCRAPING PAGE: {url}")

    # Simulate scraping and generating a summary
    await asyncio.sleep(random.uniform(0.1, 0.3))  # Simulate network delay
    dummy_summary = f"This is a dummy summary for the page {url}."

    ctx.reply(f"SCRAPING SUCCESSFUL: {url}")
    ctx.reply(Message(content=dummy_summary, metadata={"source_url": url}))


async def main():
    """
    Main function to trigger the research agent and print the results.
    Demonstrates how the flattened sequence of messages is consumed.
    """
    dummy_question = "Tell me about MiniAgents sequence flattening"

    print(f"--- Triggering research_agent with question: '{dummy_question}' ---")
    # Trigger the top-level agent. This returns a MessageSequencePromise.
    # No processing has necessarily started yet.
    response_promises: MessageSequencePromise = research_agent.trigger(dummy_question)
    print("--- research_agent triggered, response promise received ---")

    print("--- Iterating through the flattened response sequence ---")
    # As we iterate through the `response_promises` sequence, asyncio switches tasks,
    # allowing the agents (`research_agent`, `web_search_agent`, `page_scraper_agent`)
    # to run concurrently in the background and resolve their promises.
    # The `async for` loop seamlessly receives messages from the flattened sequence,
    # regardless of how deeply nested their origins were (research_agent ->
    # web_search_agent -> page_scraper_agent).
    message_counter = 0
    async for message_promise in response_promises:
        message_counter += 1
        # Await the individual message promise to get the concrete Message object.
        # For agents replying with simple strings, they are automatically wrapped
        # into Message objects.
        message: Message = await message_promise
        print(f"MESSAGE {message_counter}: {message.content}")
        if "metadata" in message:
            print(f"  Metadata: {message.metadata}")

    print("--- Iteration complete ---")
    # We can even await the whole sequence promise again to get the full list
    # of resolved messages (demonstrating the replayability of promises).
    all_messages = await response_promises
    print(f"--- Total number of messages received: {len(all_messages)} ---")


if __name__ == "__main__":
    # The MiniAgents context manager orchestrates the async execution.
    MiniAgents().run(main())
