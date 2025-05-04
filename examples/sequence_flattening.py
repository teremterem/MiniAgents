import asyncio
import random

from miniagents import InteractionContext, Message, MessageSequencePromise, MiniAgents, miniagent


@miniagent
async def research_agent(ctx: InteractionContext) -> None:
    user_question = await ctx.message_promises.as_single_text_promise()
    ctx.reply(f"RESEARCHING: {user_question}")

    dummy_search_queries = [f"Dummy Search {i+1} for '{user_question}'" for i in range(3)]

    ctx.reply(f"GENERATED {len(dummy_search_queries)} DUMMY SEARCH QUERIES.")

    all_search_results_promises = []

    for i, search_query in enumerate(dummy_search_queries):
        search_results_promise = web_search_agent.trigger(
            [ctx.message_promises, f"SEARCH CONTEXT {i+1}"],
            search_query=search_query,
        )
        all_search_results_promises.append(search_results_promise)

    ctx.reply(
        [
            "--- START OF FLATTENED SEARCH RESULTS ---",
            all_search_results_promises,
            "--- END OF FLATTENED SEARCH RESULTS ---",
        ]
    )


@miniagent
async def web_search_agent(ctx: InteractionContext, search_query: str) -> None:
    ctx.reply(f'SEARCHING FOR: "{search_query}"')

    dummy_pages_to_scrape = [f"http://dummy.page/{search_query.replace(' ', '-')}/page{i+1}" for i in range(3)]

    ctx.reply(f"FOUND {len(dummy_pages_to_scrape)} DUMMY PAGES for '{search_query}'.")

    all_scraping_results_promises = []

    for page_url in dummy_pages_to_scrape:
        scraping_results_promise = page_scraper_agent.trigger(
            [ctx.message_promises, f"SCRAPE CONTEXT for {page_url}"],
            url=page_url,
        )
        all_scraping_results_promises.append(scraping_results_promise)

    ctx.reply(
        [
            f"--- Start scraping results for '{search_query}' ---",
            all_scraping_results_promises,
            f"--- End scraping results for '{search_query}' ---",
        ]
    )


@miniagent
async def page_scraper_agent(ctx: InteractionContext, url: str) -> None:
    ctx.reply(f"SCRAPING PAGE: {url}")

    await asyncio.sleep(random.uniform(0.1, 0.3))
    dummy_summary = f"This is a dummy summary for the page {url}."

    ctx.reply(f"SCRAPING SUCCESSFUL: {url}")
    ctx.reply(Message(content=dummy_summary, metadata={"source_url": url}))


async def main():
    dummy_question = "Tell me about MiniAgents sequence flattening"

    print(f"--- Triggering research_agent with question: '{dummy_question}' ---")
    response_promises: MessageSequencePromise = research_agent.trigger(dummy_question)
    print("--- research_agent triggered, response promise received ---")

    print("--- Iterating through the flattened response sequence ---")
    message_counter = 0
    async for message_promise in response_promises:
        message_counter += 1
        message: Message = await message_promise
        print(f"MESSAGE {message_counter}: {message.content}")
        if "metadata" in message:
            print(f"  Metadata: {message.metadata}")

    print("--- Iteration complete ---")
    all_messages = await response_promises
    print(f"--- Total number of messages received: {len(all_messages)} ---")


if __name__ == "__main__":
    MiniAgents().run(main())
