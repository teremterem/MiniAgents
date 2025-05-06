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

## In this tutorial we'll use MiniAgents to build a Web Research System

<!-- <p>
    <a href="https://github.com/teremterem/MiniAgents/blob/main/examples/web_research_tutorial/web_research.py">
        <img alt="WebResearch in action"
            src="https://github.com/teremterem/MiniAgents/raw/main/images/web_research.py-x3plus.gif">
    </a>
</p> -->
<p>
    <a href="https://github.com/teremterem/MiniAgents/blob/examples/web-research-tutorial/examples/web_research_tutorial/web_research.py">
        <img alt="WebResearch in action"
            src="https://github.com/teremterem/MiniAgents/raw/examples/web-research-tutorial/images/web_research.py-x3plus.gif">
    </a>
</p>

We'll build a system that can:

1. Break down a user's question into search queries
2. Execute searches in parallel
3. Analyze the search results to identify relevant web pages
4. Scrape and extract information from those pages
5. Synthesize a comprehensive answer

***NOTE: The complete example is available [here](https://github.com/teremterem/MiniAgents/tree/main/examples/web_research_tutorial).***

# "Message Sequence Flattening"

Let's start by exploring MiniAgents's central feature - "Message Sequence Flattening". For this, we will build the first, dummy version of our Web Research System. We will not use the real LLM, will not do the actual web searching and scraping and will not create the "Final Answer" agent just yet. We'll put `asyncio.sleep()` with random delays to emulate those operations. Later in the tutorial, we will replace these delays with real web search, scraping and text generation operations.

## Naive alternative to Message Sequence Flattening

First, let's look at how you might approach this problem using standard Python async generators. This will help understand the challenges that MiniAgents solves.

```python
async def research_agent_naive(question: str) -> AsyncGenerator[str, None]:
    yield f"RESEARCHING: {question}"

    for i in range(3):
        query = f"query {i+1}"
        # NOTE: The generator below runs sequentially - "query 2" only starts
        # after "query 1" is completely finished
        async for item in web_search_agent_naive(search_query=query):
            yield item

async def web_search_agent_naive(search_query: str) -> AsyncGenerator[str, None]:
    yield f"{search_query} - SEARCHING"
    await asyncio.sleep(random.uniform(0.5, 1))
    yield f"{search_query} - SEARCH DONE"

    for i in range(2):
        url = f"https://dummy.com/{search_query.replace(' ', '-')}/page-{i+1}"
        async for item in page_scraper_agent_naive(url=url):
            yield item

async def page_scraper_agent_naive(url: str) -> AsyncGenerator[str, None]:
    yield f"{url} - SCRAPING"
    await asyncio.sleep(random.uniform(0.5, 1))
    yield f"{url} - DONE"
```

The core issue with this naive implementation is that it executes everything sequentially:

1. When the research agent processes "query 1", it must wait for all pages from that query to be fully scraped before moving on to "query 2"
2. Similarly, within each query, it processes pages one at a time
3. Once consumed, the generator is exhausted and cannot be reused:

```python
# Consume the generator once
await stream_to_stdout_naive(result_generator)

# Attempt to reuse - will yield nothing
await stream_to_stdout_naive(result_generator)
```

Here is what this process looks like as a result:

<!-- <p>
    <a href="https://github.com/teremterem/MiniAgents/blob/main/examples/sequence_flattening_naive_alternative.py">
        <img alt="WebResearch in action"
            src="https://github.com/teremterem/MiniAgents/raw/main/images/sequence_flattening_naive_alternative.py.gif">
    </a>
</p> -->
<p>
    <a href="https://github.com/teremterem/MiniAgents/blob/examples/web-research-tutorial/examples/sequence_flattening_naive_alternative.py">
        <img alt="WebResearch in action"
            src="https://github.com/teremterem/MiniAgents/raw/examples/web-research-tutorial/images/sequence_flattening_naive_alternative.py.gif">
    </a>
</p>

To achieve concurrency with standard async generators, you would need complex manual management with `asyncio.create_task()`, synchronization primitives, and state tracking - significantly increasing complexity.

## Real Sequence Flattening with MiniAgents

Now let's see how MiniAgents handles the same workflow with its sequence flattening capability:

```python
@miniagent
async def research_agent(ctx: InteractionContext) -> None:
    ctx.reply(f"RESEARCHING: {await ctx.message_promises.as_single_text_promise()}")

    for i in range(3):
        ctx.reply_out_of_order(
            # No `await` here! The agent starts executing in the background
            # and returns a MessageSequencePromise immediately
            web_search_agent.trigger(
                ctx.message_promises,
                search_query=f"query {i+1}",
            )
        )

@miniagent
async def web_search_agent(ctx: InteractionContext, search_query: str) -> None:
    ctx.reply(f"{search_query} - SEARCHING")
    await asyncio.sleep(random.uniform(0.5, 1))
    ctx.reply(f"{search_query} - SEARCH DONE")

    for i in range(2):
        ctx.reply_out_of_order(
            page_scraper_agent.trigger(
                ctx.message_promises,
                url=f"https://dummy.com/{search_query.replace(' ', '-')}/page-{i+1}",
            )
        )

@miniagent
async def page_scraper_agent(ctx: InteractionContext, url: str) -> None:
    ctx.reply(f"{url} - SCRAPING")
    await asyncio.sleep(random.uniform(0.5, 1))
    ctx.reply(f"{url} - DONE")
```

The MiniAgents approach provides several key advantages:

1. **Automatic concurrency**: All agents start working in parallel as soon as they're triggered
2. **No explicit task management**: The framework handles background execution without manual task creation
3. **Sequence flattening**: Deeply nested message hierarchies are automatically flattened into a single, uniform sequence
4. **Replayable promises**: The same sequence can be consumed multiple times

```python
# Trigger the agent - returns a MessageSequencePromise
response_promises = research_agent.trigger("Tell me about MiniAgents")

# Consume the sequence once
await stream_to_stdout(response_promises)

# Consume the SAME sequence again - works perfectly!
await stream_to_stdout(response_promises)
```

MiniAgents uses `reply()` for sequential responses and `reply_out_of_order()` when you want messages delivered as soon as they're available, rather than in strict creation order. This gives you control over message ordering while maintaining the benefits of automatic concurrency.

# Web Research System with real operations

See part 2 of the tutorial.
