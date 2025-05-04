import asyncio
import random

from miniagents import InteractionContext, MessageSequencePromise, MiniAgents, miniagent


@miniagent
async def research_agent(ctx: InteractionContext) -> None:
    ctx.reply(f"RESEARCHING: {await ctx.message_promises.as_single_text_promise()}")

    for i in range(2):
        ctx.reply(
            web_search_agent.trigger(
                ctx.message_promises,
                search_query=f"search {i+1}",
            )
        )


@miniagent
async def web_search_agent(ctx: InteractionContext, search_query: str) -> None:
    ctx.reply(f"{search_query}")
    await asyncio.sleep(random.uniform(0.1, 1))
    ctx.reply(f"{search_query} - DONE")

    for i in range(2):
        ctx.reply(
            page_scraper_agent.trigger(
                ctx.message_promises,
                url=f"http://dummy.page/{search_query.replace(' ', '-')}/page-{i+1}",
            )
        )


@miniagent
async def page_scraper_agent(ctx: InteractionContext, url: str) -> None:
    ctx.reply(f"SCRAPING: {url}")
    await asyncio.sleep(random.uniform(0.1, 1))
    ctx.reply(f"{url} - DONE")


async def stream_to_stdout(promises: MessageSequencePromise):
    i = 0
    async for message_promise in promises:
        i += 1
        print(f"{message_promise.message_class.__name__} {i}: ", end="")
        async for token in message_promise:
            print(token, end="")
        print()


async def main():
    response_promises = research_agent.trigger("Tell me about MiniAgents sequence flattening")

    print()

    await stream_to_stdout(response_promises)

    print()
    print("==============================")
    print()

    await stream_to_stdout(response_promises)

    print()
    print("==============================")
    print()

    for i, message in enumerate(await response_promises):
        print(f"{type(message).__name__} {i}: {message}")

    print()


if __name__ == "__main__":
    MiniAgents().run(main())
