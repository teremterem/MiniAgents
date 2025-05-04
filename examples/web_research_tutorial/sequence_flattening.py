"""
Sequence Flattening Example for MiniAgents

This example demonstrates the concept of "sequence flattening" in MiniAgents, which is one
of the framework's central features. Sequence flattening automatically resolves complex
hierarchical structures of messages, promises, and collections into flat, uniform sequences
of message promises in the background.

The example mimics the structure of the web_research.py example but uses dummy messages
instead of real web searches, scraping, and LLM calls to focus on the sequence flattening concept.
"""

import asyncio
from typing import Set

from miniagents import AgentCall, InteractionContext, Message, MessageSequencePromise, MiniAgents, miniagent


@miniagent
async def research_agent(ctx: InteractionContext) -> None:
    """
    Main research agent that coordinates the entire workflow.

    This agent demonstrates sequence flattening by creating a complex hierarchy of messages:
    1. It generates direct text replies
    2. It triggers sub-agents that generate their own sequences of messages
    3. It forwards responses from multiple agents to another agent

    All of these different message types and sources get automatically flattened into
    a single, uniform sequence of messages that can be consumed by the caller.
    """
    # Reply with a simple string - this will be automatically converted to a Message object
    ctx.reply("STARTING RESEARCH PROCESS...")

    # Let's pretend we've analyzed the user's question and generated 3 search queries
    search_queries = [
        {"query": "search query 1", "rationale": "reason for search 1"},
        {"query": "search query 2", "rationale": "reason for search 2"},
        {"query": "search query 3", "rationale": "reason for search 3"},
    ]

    ctx.reply(f"RUNNING {len(search_queries)} SEARCH QUERIES")

    # Set to track URLs we've already seen to avoid duplicates
    already_picked_urls = set()

    # Fork the web_search_agent to introduce mutable state
    # (we want it to remember which URLs were already picked)
    _web_search_agent = web_search_agent.fork(
        non_freezable_kwargs={
            "already_picked_urls": already_picked_urls,
        },
    )

    # Initiate a call to the final answer agent (unlike trigger, initiate_call
    # does not require all input messages upfront)
    final_answer_call: AgentCall = final_answer_agent.initiate_call(
        # Pass the original user question as a keyword argument
        user_question=await ctx.message_promises,
    )

    # For each search query, trigger a web search agent
    # Note: No await means these are all scheduled in parallel
    for search in search_queries:
        # Each web_search_agent.trigger() returns a MessageSequencePromise
        search_results = _web_search_agent.trigger(
            ctx.message_promises,
            search_query=search["query"],
            rationale=search["rationale"],
        )

        # SEQUENCE FLATTENING EXAMPLE 1:
        # Replying with a MessageSequencePromise (search_results) will automatically
        # flatten it into the current agent's output sequence. Messages from search_results
        # will appear in the research_agent's output as if they were directly sent by it.
        ctx.reply_out_of_order(search_results)

        # Also send these results to the final answer agent
        final_answer_call.send_message(search_results)

    # SEQUENCE FLATTENING EXAMPLE 2:
    # Replying with the final_answer_call.reply_sequence() (another MessageSequencePromise)
    # will also be flattened into the current agent's output sequence.
    ctx.reply(final_answer_call.reply_sequence())

    # This message will be part of the same flattened sequence
    ctx.reply("RESEARCH PROCESS COMPLETE!")


@miniagent
async def web_search_agent(
    ctx: InteractionContext,
    search_query: str,
    rationale: str,
    already_picked_urls: Set[str],
) -> None:
    """
    Agent that simulates web searches and identifies pages to be scraped.

    This agent demonstrates sequence flattening by:
    1. Generating direct messages about the search process
    2. Triggering multiple page_scraper_agents and incorporating their results

    These nested results get flattened into the agent's output sequence.
    """
    # Reply with information about what we're searching for
    ctx.reply(f'SEARCHING FOR "{search_query}"\n{rationale}')

    # Simulate a delay for the search
    await asyncio.sleep(0.5)

    # Pretend we found some search results
    ctx.reply(f"SEARCH SUCCESSFUL: {search_query}")

    # Simulate finding 3 pages to scrape for each search query
    pages_to_scrape = [
        {"url": f"{search_query}_page_{i}", "rationale": f"reason for scraping page {i}"} for i in range(1, 4)
    ]

    # Filter out pages we've already seen
    unseen_pages = []
    for page in pages_to_scrape:
        if page["url"] not in already_picked_urls:
            unseen_pages.append(page)
            already_picked_urls.add(page["url"])

    # SEQUENCE FLATTENING EXAMPLE 3:
    # Trigger scraping for each identified page
    # The responses from these agents will be flattened into our response
    for page in unseen_pages:
        # Each page_scraper_agent.trigger() returns a MessageSequencePromise
        scraping_results = page_scraper_agent.trigger(
            ctx.message_promises,
            url=page["url"],
            rationale=page["rationale"],
        )

        # reply_out_of_order also demonstrates sequence flattening - all messages
        # from scraping_results will be flattened into the web_search_agent's output
        ctx.reply_out_of_order(scraping_results)


@miniagent
async def page_scraper_agent(
    ctx: InteractionContext,
    url: str,
    rationale: str,
) -> None:
    """
    Agent that simulates scraping web pages.

    This is a leaf agent that just returns simple messages.
    """
    # Report that we're reading a page
    ctx.reply(f"READING PAGE: {url}\n{rationale}")

    # Simulate a delay for scraping
    await asyncio.sleep(0.3)

    # Report success
    ctx.reply(f"SCRAPING SUCCESSFUL: {url}")

    # Simulate extracting content from the page
    ctx.reply(f"CONTENT SUMMARY FROM {url}: This is pretend content from the page.")


@miniagent
async def final_answer_agent(ctx: InteractionContext, user_question: Message) -> None:
    """
    Agent that synthesizes all the collected information into a final answer.

    This agent waits for all input before generating its response.
    """
    # Wait for all input messages to arrive before proceeding
    # (all the search and scraping results)
    await ctx.message_promises

    # Add a separator to indicate the start of the answer
    ctx.reply("==========\nFINAL ANSWER:\n==========")

    # Simulate generating an answer based on the collected information
    # In reality, this would use an LLM to synthesize the information
    ctx.reply(
        f"Based on the research conducted for the question '{await user_question}', "
        f"here is a synthesized answer using information from multiple sources."
    )


async def main():
    """
    Main function that triggers the research agent and prints the results.

    This demonstrates how the complex hierarchy of agents and message sequences
    ultimately gets flattened into a single sequence that the caller can consume.
    """
    question = "What is sequence flattening in MiniAgents?"

    # Trigger the research agent
    response_promises: MessageSequencePromise = research_agent.trigger(question)

    print("\n")
    # Iterate over the messages in the response sequence
    # Even though internally there's a complex tree of agents calling each other,
    # what we get here is a flat sequence of messages thanks to sequence flattening
    async for message_promise in response_promises:
        # Get the actual message content
        message = await message_promise
        print(message)
        print()  # Add a blank line between messages

    print("All messages have been processed and flattened into a single sequence.")


if __name__ == "__main__":
    # Run everything within the MiniAgents context
    MiniAgents(
        # Make agent errors appear as messages in the output instead of raising exceptions
        errors_as_messages=True,
    ).run(main())
