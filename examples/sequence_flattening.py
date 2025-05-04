"""
Sequence Flattening Example for MiniAgents

This example demonstrates the concept of "sequence flattening" in MiniAgents, which is one
of the framework's central features. Sequence flattening automatically resolves complex
hierarchical structures of messages, promises, and collections into flat, uniform sequences
of message promises in the background.

The example mimics the structure of the web_research.py example but uses dummy messages
instead of real web searches, scraping, and LLM calls to focus on the sequence flattening
concept.

NOTE: Sequence flattening happens both, when you pass input to an agent (could be concrete
messages, could be promises, could be collections of either of the two), and when an agent
replies with a promise of a message promise sequence (MessageSequencePromise).
"""

import asyncio
import random

from miniagents import InteractionContext, Message, MessageSequencePromise, MiniAgents, miniagent


@miniagent
async def research_agent(ctx: InteractionContext) -> None:
    """
    The main research agent.
    It receives the initial request (a dummy question in this example).
    It pretends to break the request down into dummy "search queries".
    For each search query, it triggers the web_search_agent.

    Crucially, it collects the results (which are MessageSequencePromise objects)
    from the web_search_agent and includes them directly in its own reply sequence.
    """
    ctx.reply(f"RESEARCHING: {await ctx.message_promises.as_single_text_promise()}")
    # NOTE: `ctx.reply()` accepts lists (or other iterables) of items. These items can be:
    #   - Concrete messages (like strings, TextMessage objects, or other Message objects)
    #   - Promises of individual messages (MessagePromise)
    #   - Promises of sequences of messages promises (MessageSequencePromise)
    # MiniAgents automatically resolves and flattens this nested structure in the
    # background. The consumer of `research_agent`'s response sequence (in this
    # case, the `main` function) will receive a single, flat sequence of messages
    # as if all the messages from the nested sequences were yielded directly by
    # `research_agent`.

    for i in range(3):
        # TODO explain how `ctx.reply_out_of_order()` is different from `ctx.reply()`
        ctx.reply_out_of_order(
            # Trigger the web_search_agent for each query.
            # IMPORTANT: No `await` here! `trigger` returns immediately with a
            # `MessageSequencePromise`. The actual execution of `web_search_agent`
            # will start in the background when asyncio gets a chance to switch tasks.
            web_search_agent.trigger(
                # Pass the original question to `web_search_agent`, so it knows what
                # to pay attention to (it will not be used yet, as it is a dummy
                # implementation)
                ctx.message_promises,
                # Pass the search query as a keyword argument
                search_query=f"query {i+1}",
            )
        )


@miniagent
async def web_search_agent(ctx: InteractionContext, search_query: str) -> None:
    """
    Pretends to perform a web search for a given query and identify pages to scrape.
    For each dummy page URL, it triggers the page_scraper_agent.

    It collects the results (MessageSequencePromise objects) from the page_scraper_agent
    and includes them in its own reply sequence. This nesting will be flattened into a
    single sequence in the background.
    """
    ctx.reply(f"{search_query} - SEARCHING")
    await asyncio.sleep(random.uniform(0.1, 1))
    ctx.reply(f"{search_query} - DONE")

    for i in range(3):
        # TODO `ctx.reply_out_of_order()` again
        ctx.reply_out_of_order(
            # Trigger the page_scraper_agent for each dummy URL.
            # Again, no `await` - MessageSequencePromise will be returned immediately.
            page_scraper_agent.trigger(
                # Pass the original question to `page_scraper_agent`, so it knows what
                # to pay attention to (it will not be used yet, as it is a dummy
                # implementation)
                ctx.message_promises,
                # Pass the dummy URL as a keyword argument
                url=f"http://dummy.page/{search_query.replace(' ', '-')}/page-{i+1}",
            )
        )


@miniagent
async def page_scraper_agent(ctx: InteractionContext, url: str) -> None:
    """
    Pretends to scrape a web page and extract information. Replies with simple
    status messages.

    This is the innermost agent in this example. Its replies will be flattened
    into web_search_agent's sequence, and then into research_agent's sequence.
    """
    ctx.reply(f"{url} - SCRAPING")
    await asyncio.sleep(random.uniform(0.1, 1))
    ctx.reply(f"{url} - DONE")


async def stream_to_stdout(promises: MessageSequencePromise):
    """
    As we iterate through the `response_promises` sequence, asyncio switches tasks,
    allowing the agents (`research_agent`, `web_search_agent`, `page_scraper_agent`)
    to run concurrently in the background and resolve their promises.
    The `async for` loop seamlessly receives messages from the flattened sequence,
    regardless of how deeply nested their origins were (research_agent ->
    web_search_agent -> page_scraper_agent).
    """
    i = 0
    async for message_promise in promises:
        i += 1
        print(f"{message_promise.message_class.__name__} {i}: ", end="")
        async for token in message_promise:
            print(token, end="")
        print()

        # # You could also await for a complete message if you didn't care about
        # # streaming:
        # message: Message = await message_promise
        # print(message)


async def main():
    """
    Main function to trigger the research agent and print the results.
    Demonstrates how the flattened sequence of messages is consumed.
    """
    # Trigger the top-level agent. This returns a MessageSequencePromise.
    # No processing has started yet.
    response_promises = research_agent.trigger("Tell me about MiniAgents sequence flattening")

    print()

    await stream_to_stdout(response_promises)

    print()
    print("==============================")
    print()

    # If we iterate through the sequence again, we will see that exactly same messages
    # are yielded again (and in exactly the same order). This demonstrates the
    # replayability of all types of promises in MiniAgents.
    await stream_to_stdout(response_promises)

    print()
    print("==============================")
    print()

    # We can even await the whole sequence promise again to get the full list
    # of resolved messages (demonstrating the replayability of promises once again).
    messages: tuple[Message, ...] = await response_promises
    for i, message in enumerate(messages):
        # When you run this example, you will see that for agents replying with
        # simple strings, they are automatically wrapped into TextMessage objects
        # (a subclass of Message).
        print(f"{type(message).__name__} {i+1}: {message}")

    print()


if __name__ == "__main__":
    # The MiniAgents context manager orchestrates the async execution.
    MiniAgents().run(main())
