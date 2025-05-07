# MiniAgents: Multi-Agent AI With Procedural Simplicity

![MiniAgents on Mars](https://github.com/teremterem/MiniAgents/raw/main/images/banner-miniagents-2025-04-27.jpeg)

An open-source, async-first Python framework for building multi-agent AI systems with an innovative approach to parallelism, so you can focus on creating intelligent agents, not on managing the concurrency of your flows.

To install MiniAgents run the following command:

```bash
pip install -U miniagents
```

The source code of the project is hosted on [GitHub](https://github.com/teremterem/MiniAgents).

## Why MiniAgents

1. **Write procedural code, get parallel execution:** Unlike graph-based frameworks that force you to think in nodes and edges, MiniAgents lets you write straightforward sequential code while the framework handles parallelism automatically. Your code stays clear and readable.

2. **Nothing blocks until it's needed:** With its innovative promise-based architecture, agents execute in parallel and the execution gets blocked only at the points where specific agent messages are required. Agents communicate through ***replayable promises of message sequences***, not concrete messages, allowing maximum concurrency without complex synchronization code.

3. **Immutable message philosophy:** MiniAgents uses immutable, Pydantic-based messages that eliminate race conditions and data corruption concerns. This design choice enables highly parallelized agent execution without the headaches of state management.

4. **Sequential code, parallel execution:** The framework's unique approach to agent communication through sequence promises means your code can look completely sequential while actually running in parallel:

```python
@miniagent
async def aggregator_agent(ctx: InteractionContext) -> None:
    # This looks sequential but all agents start working in parallel
    ctx.reply([
        # All nested sequences here will be asynchronously "flattened" in the background
        # for an outside agent (i.e., the one triggering the `aggregator_agent`), so that
        # when the outside agent consumes the result, it appears as a single, flat sequence
        # of messages.
        "Starting analysis...",
        research_agent.trigger(ctx.message_promises),
        calculation_agent.trigger(ctx.message_promises),
        "Analysis complete!",
    ])
```

# Let's build a Web Research System with MiniAgents

<!-- <p>
    <a href="https://github.com/teremterem/MiniAgents/blob/main/examples/web_research_tutorial">
        <img alt="WebResearch in action"
            src="https://github.com/teremterem/MiniAgents/raw/main/images/web_research.py-x3plus.gif">
    </a>
</p> -->
<p>
    <a href="https://github.com/teremterem/MiniAgents/blob/examples/web-research-tutorial/examples/web_research_tutorial">
        <img alt="WebResearch in action"
            src="https://github.com/teremterem/MiniAgents/raw/examples/web-research-tutorial/images/web_research.py-x3plus.gif">
    </a>
</p>

In this tutorial we'll build a system that can:

1. Break down a user's question into search queries
2. Execute searches in parallel
3. Analyze the search results to identify relevant web pages
4. Scrape and extract information from those pages
5. Synthesize a comprehensive answer

The animation above demonstrates what the output of this system will look like.

<!-- ***NOTE: The complete source code is available [here](https://github.com/teremterem/MiniAgents/tree/main/examples/web_research_tutorial).*** -->

***NOTE: The complete source code is available [here](https://github.com/teremterem/MiniAgents/tree/examples/web-research-tutorial/examples/web_research_tutorial).***

## "Message Sequence Flattening"

Let's start by exploring MiniAgents's central feature - "Message Sequence Flattening". For this, we will build the first, dummy version of our Web Research System. We will not use the real LLM, will not do the actual web searching and scraping and will not create the "Final Answer" agent just yet. We'll put `asyncio.sleep()` with random delays to emulate those operations. Later in the tutorial, we will replace these delays with real web search, scraping and text generation operations.

### Naive alternative to Message Sequence Flattening

First, let's look at how you might approach this problem using standard Python async generators. This will help understand the challenges that MiniAgents solves.

This approach uses standard Python `async def` with `async for ... yield` to simulate how one might try to build a similar system without MiniAgents. The key thing to note here is that this method leads to **sequential execution** of the "agents" (async generators in this case).

The full code for this naive example can be found in [`sequence_flattening_naive_alternative.py`](https://github.com/teremterem/MiniAgents/blob/main/examples/sequence_flattening_naive_alternative.py).

Let's look at the core agent definitions:

```python
# examples/sequence_flattening_naive_alternative.py
import asyncio
import random
from typing import AsyncGenerator


async def research_agent_naive(question: str) -> AsyncGenerator[str, None]:
    """
    The main research agent, implemented naively.
    Calls web_search_agent_naive sequentially.
    """
    yield f"RESEARCHING: {question}"

    for i in range(3):
        query = f"query {i+1}"
        # The `async for ... yield` construct processes the generator
        # sequentially. The `web_search_agent_naive` for "query 2" will only
        # start after the one for "query 1" (including all its pretend-scraping)
        # is finished.
        async for item in web_search_agent_naive(search_query=query):
            yield item


async def web_search_agent_naive(search_query: str) -> AsyncGenerator[str, None]:
    """
    Pretends to perform a web search and trigger scraping.
    Calls page_scraper_agent_naive sequentially.
    """
    yield f"{search_query} - SEARCHING"
    await asyncio.sleep(random.uniform(0.5, 1))
    yield f"{search_query} - SEARCH DONE"

    for i in range(2):
        url = f"https://dummy.com/{search_query.replace(' ', '-')}/page-{i+1}"
        # This leads to sequential execution. The next iteration or yield
        # only happens *after* page_scraper_agent_naive is completely finished.
        async for item in page_scraper_agent_naive(url=url):
            yield item


async def page_scraper_agent_naive(url: str) -> AsyncGenerator[str, None]:
    """
    Pretends to scrape a web page.
    """
    yield f"{url} - SCRAPING"
    await asyncio.sleep(random.uniform(0.5, 1))
    yield f"{url} - DONE"

# ... (main_naive and stream_to_stdout_naive)
```
In `research_agent_naive`, the loop that calls `web_search_agent_naive` processes each "search query" one after the other. The comment inside the loop explicitly points this out: `web_search_agent_naive` for "query 2" will only begin after "query 1" and all its subsequent operations (like page scraping) are entirely finished.

Similarly, `web_search_agent_naive` waits for `page_scraper_agent_naive` to complete for one URL before processing the next. This is because `async for item in sub_generator:` effectively awaits the completion of `sub_generator`'s items sequentially.

To achieve true concurrency with this naive approach, you would need to manually manage `asyncio.create_task` for each sub-operation and potentially use queues or other synchronization primitives to collect and yield results as they become available. This would significantly increase code complexity.

Furthermore, standard async generators, once consumed, are exhausted. If you try to iterate over the `result_generator` in `main_naive` a second time, it will yield nothing. This contrasts with MiniAgents' replayable promises.

### Real Message Sequence Flattening with MiniAgents

Now, let's see how MiniAgents addresses these challenges, enabling concurrent execution with simpler, more declarative code.

The full code for this MiniAgents example can be found in [`sequence_flattening.py`](https://github.com/teremterem/MiniAgents/blob/main/examples/sequence_flattening.py).

Here are the agent definitions using MiniAgents:

```python
# examples/sequence_flattening.py
import asyncio
import random

from miniagents import InteractionContext, MessageSequencePromise, MiniAgents, miniagent


@miniagent
async def research_agent(ctx: InteractionContext) -> None:
    ctx.reply(f"RESEARCHING: {await ctx.message_promises.as_single_text_promise()}")

    for i in range(3):
        # `trigger` returns immediately with a `MessageSequencePromise`.
        # The actual execution of `web_search_agent` starts in the background.
        # `reply_out_of_order` delivers messages as they become available,
        # not strictly in the order they are added to the reply.
        ctx.reply_out_of_order(
            web_search_agent.trigger(
                ctx.message_promises, # Original question
                search_query=f"query {i+1}",
            )
        )


@miniagent
async def web_search_agent(ctx: InteractionContext, search_query: str) -> None:
    ctx.reply(f"{search_query} - SEARCHING")
    await asyncio.sleep(random.uniform(0.5, 1)) # Simulate work
    ctx.reply(f"{search_query} - SEARCH DONE")

    for i in range(2):
        # Again, no `await` here when triggering the next agent.
        # The page_scraper_agent will run in parallel.
        ctx.reply_out_of_order(
            page_scraper_agent.trigger(
                ctx.message_promises, # Original question
                url=f"https://dummy.com/{search_query.replace(' ', '-')}/page-{i+1}",
            )
        )


@miniagent
async def page_scraper_agent(ctx: InteractionContext, url: str) -> None:
    ctx.reply(f"{url} - SCRAPING")
    await asyncio.sleep(random.uniform(0.5, 1)) # Simulate work
    ctx.reply(f"{url} - DONE")

# ... (stream_to_stdout and main)
```

In the MiniAgents version:
1.  When `research_agent` calls `web_search_agent.trigger(...)`, this call is non-blocking. It immediately returns a `MessageSequencePromise`. The actual execution of `web_search_agent` (and any agents it subsequently triggers) begins in the background when the asyncio event loop gets a chance to switch tasks.
2.  The `ctx.reply(...)` method (and its variant `ctx.reply_out_of_order(...)`) is versatile. It can accept:
    *   Concrete messages (like strings, which are automatically wrapped, or `Message` objects).
    *   Promises of individual messages (`MessagePromise`).
    *   Promises of sequences of messages (`MessageSequencePromise`), such as those returned by `agent.trigger()`.
3.  MiniAgents automatically "flattens" this potentially deeply nested structure of messages and promises. When the `main` function (or another agent) consumes the `response_promises` from `research_agent`, it receives a single, flat sequence of all messages. This sequence includes messages produced directly by `research_agent`, all messages from all the triggered `web_search_agent` instances, and consequently, all messages from all the `page_scraper_agent` instances called by them.
4.  The `async for message_promise in promises:` loop in the `stream_to_stdout` function (which consumes the results in `main`) allows asyncio to switch tasks effectively. This enables the agents (`research_agent`, `web_search_agent`, `page_scraper_agent`) to run concurrently in the background. Messages appear in the output stream as they are produced by these parallel operations, rather than waiting for a whole chain of calls to complete. The `reply_out_of_order` usage ensures that messages are yielded as soon as they are ready, further enhancing the sense of parallelism from the consumer's perspective, though it doesn't change the parallelism of the actual agent execution (which is already parallel due to `trigger` being non-blocking).
5.  A key feature highlighted in the `main` function of `sequence_flattening.py` is the **replayability** of `MessageSequencePromise` objects. You can iterate over `response_promises` multiple times and get the exact same sequence of messages. This is invaluable for scenarios where you might want to feed the same set of results to multiple different subsequent processing agents without worrying about "exhausting" the input stream.

This automatic concurrency and sequence flattening greatly simplify the development of complex, multi-step AI systems. You can focus on the logic of each individual agent, writing code that appears sequential within the agent, while the MiniAgents framework handles the parallel execution and complex data flow management behind the scenes.

## Web Research System with real operations

Please see part 2 of this tutorial.
