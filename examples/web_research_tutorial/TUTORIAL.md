# MiniAgents: Multi-Agent AI With Procedural Simplicity

![MiniAgents on Mars](https://github.com/teremterem/MiniAgents/raw/main/images/banner-miniagents-2025-04-27.jpeg)

An open-source, async-first Python framework for building multi-agent AI systems with an innovative approach to parallelism, so you can focus on creating intelligent agents, not on managing the concurrency of your flows.

To install MiniAgents run the following command:

```bash
pip install -U miniagents
```

The source code of the project is hosted on [GitHub](https://github.com/teremterem/MiniAgents).

## Why MiniAgents

1. **Write procedural code, get parallel execution:** Unlike graph-based frameworks that often require defining explicit nodes and edges for control flow, or general-purpose async libraries like `trio` or `anyio` where you'd manually manage task creation and synchronization (TODO is it really useful to bring up `trio` or `anyio` here ?), MiniAgents lets you write straightforward sequential code while the framework handles the complexities of parallel execution for agent interactions automatically. Your code stays clear and readable, focusing on agent logic rather than low-level concurrency plumbing.

2. **Nothing blocks until it's needed:** With its innovative promise-based architecture, agents execute in parallel. Execution only blocks at points where specific agent messages are actively awaited. Agents communicate through ***replayable promises of message sequences***, not just concrete messages or single-pass async generators. This replayability is a key distinction, allowing message streams to be consumed multiple times by different agents or for different purposes, fostering flexible data flows and enabling maximum concurrency without complex manual synchronization code.

3. **Immutable message philosophy:** MiniAgents uses immutable, Pydantic-based messages that eliminate race conditions and data corruption concerns. This design choice enables highly parallelized agent execution without the headaches of state management. (TODO mention that state management is still possible)

4. **Sequential code, parallel execution:** The framework's unique approach to agent communication through sequence promises means your code can look completely sequential while actually running in parallel (TODO 4 is actually a duplicate of 1):

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

Let's start by exploring MiniAgents' central feature - "Message Sequence Flattening". For this, we will build the first, dummy version of our Web Research System. We will not use the real LLM, will not do the actual web searching and scraping and will not create the "Final Answer" agent just yet. We'll put `asyncio.sleep()` with random delays to emulate those operations. Later in the tutorial, we will replace these delays with real web search, scraping and text generation operations.

### Naive alternative to "Message Sequence Flattening"

TODO either explain what Message Sequence Flattening is right away or promise that you will explain it later.

First, let's look at how you might approach this problem (TODO what problem ?!) using standard Python async generators. This will help understand the challenges that MiniAgents solves.

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

# TODO don't skip stuff
# ... (main_naive and stream_to_stdout_naive)
```
In `research_agent_naive`, the loop that calls `web_search_agent_naive` processes each "search query" one after the other. The comment inside the loop explicitly points this out: `web_search_agent_naive` for "query 2" will only begin after "query 1" and all its subsequent operations (like page scraping) are entirely finished.

Similarly, `web_search_agent_naive` waits for `page_scraper_agent_naive` to complete for one URL before processing the next. This is because `async for item in sub_generator:` effectively awaits the completion of `sub_generator`'s items sequentially.

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

To achieve true concurrency with this naive approach, you would need to manually manage `asyncio.create_task` for each sub-operation and potentially use queues or other synchronization primitives to collect and yield results as they become available. This would significantly increase code complexity.

Furthermore, standard async generators, once consumed, are exhausted. If you try to iterate over the `result_generator` in `main_naive` a second time, it will yield nothing. This contrasts with MiniAgents' replayable promises.

This manual management is typical when using raw `asyncio` or even foundational async libraries like `trio` or `anyio`. While these libraries provide powerful concurrency tools, MiniAgents aims to provide a higher-level, agent-centric abstraction for these patterns, particularly around how agents stream and combine their results.

### Real "Message Sequence Flattening" with MiniAgents

TODO move the "Real Sequence Flattening" animation here, so it is easier to compare with the animation above.

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

# TODO don't skip these two functions ?
# ... (stream_to_stdout and main)
```

In the MiniAgents version:
1.  When `research_agent` calls `web_search_agent.trigger(...)`, this call is non-blocking. It immediately returns a `MessageSequencePromise`. The actual execution of `web_search_agent` (and any agents it subsequently triggers) begins in the background when the asyncio event loop gets a chance to switch tasks.
2.  The `ctx.reply(...)` method (and its variant `ctx.reply_out_of_order(...)`) is versatile. It can accept:
    *   Concrete messages, like strings, dicts or arbitrary Pydantic objects, which are automatically wrapped into either `Message` or `TextMessage` by the framework, or `Message` objects (and subclasses thereof) directly. TODO this sentence is a mess
    *   Promises of individual messages (`MessagePromise`).
    *   Promises of sequences of message promises (TODO confusing ?; `MessageSequencePromise`), such as those returned by `agent.trigger()`.
    *   Collections (lists, tuples, etc.) of all of the above.
3.  MiniAgents automatically "flattens" this potentially deeply nested structure of messages and promises. When the `main` function (or another agent) consumes the `response_promises` from `research_agent`, it receives a single, flat sequence of all messages. This sequence includes messages produced directly by `research_agent`, all messages from all the triggered `web_search_agent` instances, and consequently, all messages from all the `page_scraper_agent` instances called by them.
4.  The `async for message_promise in promises:` loop in the `stream_to_stdout` function (which consumes the results in `main`) allows asyncio to switch tasks effectively (TODO the word effectively sounds confusing here - what would non-effective task switching look like ?). This enables the agents (`research_agent`, `web_search_agent`, `page_scraper_agent`) to run concurrently in the background. Messages appear in the output stream as they are produced by these parallel operations, rather than waiting for a whole chain of calls to complete (TODO `reply_out_of_order` should be mentioned before this sentence, not after). The `reply_out_of_order` usage ensures that messages are yielded as soon as they are ready, further enhancing the sense of parallelism from the consumer's perspective, though it doesn't change the parallelism of the actual agent execution (which is already parallel due to `trigger` being non-blocking).
5.  A key feature highlighted in the `main` function of `sequence_flattening.py` is the **replayability** of `MessageSequencePromise` objects. You can iterate over `response_promises` multiple times and get the exact same sequence of messages. This is invaluable for scenarios where you might want to feed the same set of results to multiple different subsequent processing agents without worrying about "exhausting" the input stream.

TODO does the text below play well with text above ?

If you look at the output of the above code, you'll see that processing happens much faster, even though we didn't do anything special to achieve that, all thanks to parallelism introduced by the framework:

<!-- <p>
    <a href="https://github.com/teremterem/MiniAgents/blob/main/examples/sequence_flattening.py">
        <img alt="WebResearch in action"
            src="https://github.com/teremterem/MiniAgents/raw/main/images/sequence_flattening.py.gif">
    </a>
</p> -->
<p>
    <a href="https://github.com/teremterem/MiniAgents/blob/examples/web-research-tutorial/examples/sequence_flattening.py">
        <img alt="WebResearch in action"
            src="https://github.com/teremterem/MiniAgents/raw/examples/web-research-tutorial/images/sequence_flattening.py.gif">
    </a>
</p>

This automatic concurrency and sequence flattening greatly simplify the development of complex, multi-step AI systems. You can focus on the logic of each individual agent, writing code that appears sequential within the agent, while the MiniAgents framework handles the parallel execution and complex data flow management behind the scenes.

## Web Research System with real operations

Now that we've explored the core concept of "Message Sequence Flattening" with a dummy example, let's dive into the fully functional Web Research System. This system uses real AI models for understanding and generation, performs actual web searches, and scrapes web pages to gather information.

The complete source code for this example can be found in [`web_research.py`](https://github.com/teremterem/MiniAgents/blob/examples/web-research-tutorial/examples/web_research_tutorial/web_research.py).

### Prerequisites

Before running the `web_research.py` script, you'll need to set up a few things:

1.  **Environment Variables:** The system uses Bright Data for web searching (via their SERP API) and web scraping (via their Scraping Browser). You'll need to sign up for these services and obtain API credentials. Create a `.env` file in the project root directory (or the same directory as `web_research.py`) with your credentials:

    ```env
    # .env
    BRIGHTDATA_SERP_API_CREDS="your_serp_api_username:your_serp_api_password"
    BRIGHTDATA_SCRAPING_BROWSER_CREDS="your_scraping_browser_username:your_scraping_browser_password"
    OPENAI_API_KEY="your_openai_api_key"
    ```
    TODO mention that those aren't global user credentials

2.  **Helper Utilities (`utils.py`):** The project uses a `utils.py` file (available [here](https://github.com/teremterem/MiniAgents/blob/examples/web-research-tutorial/examples/web_research_tutorial/utils.py)) which contains helper functions for:
    *   `fetch_google_search()`: Interacts with the Bright Data SERP API.
    *   `scrape_web_page()`: Uses Selenium with Bright Data's Scraping Browser to fetch and parse web page content. It runs Selenium in a separate thread pool as Selenium is blocking.
    *   `check_miniagents_version()`: Ensures you have a compatible version of MiniAgents.

    You don't need to dive deep into `utils.py` to understand the MiniAgents framework, but it's essential for the example to run.

### System Overview and the `main` function

The entry point of our application is the `main()` function. It orchestrates the entire process:

```python
# examples/web_research_tutorial/web_research.py
# TODO don't skip stuff
# ... (imports and setup) ...

async def main():
    question = input("\nEnter your question: ")

    # Invoke the main agent (no `await` is placed in front of the call, hence this is a non-blocking operation, no
    # processing starts just yet)
    response_promises: MessageSequencePromise = research_agent.trigger(question)

    print()
    # Iterate over the individual message promises in the response sequence promise. The async loops below lead to task
    # switching, so the agent above as well as its "sub-agents" will now start their work in the background to serve
    # all the promises.
    async for message_promise in response_promises:
        # Skip messages that are not intended for the user (you'll see where the `not_for_user` attribute is set later)
        if message_promise.known_beforehand.get("not_for_user"):
            continue
        # Iterate over the individual tokens in the message promise (messages that aren't broken down into tokens will
        # be delivered in a single token)
        async for token in message_promise:
            print(token, end="", flush=True)
        print("\n")

# TODO don't skip stuff ?
# ... (rest of the file)
```

Key takeaways from `main()`:
1.  **Non-Blocking Trigger:** `research_agent.trigger(question)` is called without `await`. This immediately returns a `MessageSequencePromise`, and the `research_agent` (and any agents it triggers) will start processing in the background when the event loop allows.
2.  **Streaming Responses:** The `async for message_promise in response_promises:` loop iterates through the promised messages. Crucially, this loop allows `asyncio` to switch tasks. As messages (or even tokens within messages, if streaming is enabled for an LLM agent) become available from the agent system, they are printed to the console.
3.  **Filtering Messages:** Some messages might be internal to the agent system (e.g., detailed summaries for other agents). We can attach metadata to messages (like `not_for_user`) and use it to filter what's shown to the end-user.
4.  **Centralized Output:** Notice that all user-facing output happens here. Agents themselves don't `print`. They communicate results back, which `main` then decides how to present. This separation makes it easier to change the UI or integrate the agent system elsewhere (TODO more emphasis on possibility to integrate it as part of a bigger AI system).
5.  **Automatic Background Execution:** MiniAgents, by default, starts processing triggered agents as soon as possible. This is generally the desired behavior for maximum parallelism. While you *can* control this with `start_soon=False` in `trigger` calls or globally (TODO mention global parameter name), it's often unnecessary and can complicate agent interdependencies (TODO the actual problem is deadlocks).

### The `research_agent`: Orchestrating the Search

The `research_agent` is the primary coordinator. It takes the user's question and breaks it down into actionable steps.

```python
# examples/web_research_tutorial/web_research.py
# TODO don't skip stuff ?
# ... (imports and setup) ...

@miniagent
async def research_agent(ctx: InteractionContext) -> None:
    ctx.reply("RESEARCHING...")

    # First, analyze the user's question and break it down into search queries
    message_dicts = await aprepare_dicts_for_openai(
        ctx.message_promises, # The user's question
        system=(
            "Your job is to breakdown the user's question into a list of web searches that need to be done to answer "
            "the question. Please try to optimize your search queries so there aren't too many of them. Current date "
            "is " + datetime.now().strftime("%Y-%m-%d")
        ),
    )
    # Using OpenAI's client library directly for structured output
    # TODO mention that MiniAgents will later support it natively
    response = await openai_client.beta.chat.completions.parse(
        model=SMARTER_MODEL,
        messages=message_dicts,
        response_format=WebSearchesToBeDone, # Pydantic model for structured output
    )
    parsed: WebSearchesToBeDone = response.choices[0].message.parsed

    ctx.reply(f"RUNNING {len(parsed.web_searches)} WEB SEARCHES")

    already_picked_urls = set[str]()
    # Fork the `web_search_agent` to give it mutable state for this specific research task
    _web_search_agent = web_search_agent.fork(
        non_freezable_kwargs={
            "already_picked_urls": already_picked_urls,
        },
    )

    # Initiate a call to the final_answer_agent. We'll send it data as we gather it.
    final_answer_call: AgentCall = final_answer_agent.initiate_call(
        user_question=await ctx.message_promises,
    )

    # For each identified search query, trigger a web search agent
    for web_search in parsed.web_searches:
        search_and_scraping_results = _web_search_agent.trigger(
            ctx.message_promises, # Forwarding the original user question
            search_query=web_search.web_search_query,
            rationale=web_search.rationale,
        )
        # `reply_out_of_order` sends messages to the research_agent's output
        # as they become available, maintaining responsiveness.
        ctx.reply_out_of_order(search_and_scraping_results)

        # Send the same results to the final_answer_agent
        final_answer_call.send_message(search_and_scraping_results)

    # Reply with the sequence from final_answer_agent, effectively chaining its output
    # to research_agent's output. This also closes the call to final_answer_agent.
    ctx.reply(final_answer_call.reply_sequence())

# TODO don't skip stuff ?
# ... (other agents)
```

Key aspects of `research_agent`:
1.  **Query Generation:** It uses an LLM (via `openai_client.beta.chat.completions.parse`) to break the user's question into a list of specific search queries. `WebSearchesToBeDone` is a Pydantic model that ensures the LLM returns data in the expected structure. TODO de-emphasize because it is not a feature of MiniAgents (yet)
2.  **Agent Forking for State:** The `web_search_agent` needs to keep track of URLs it has already decided to scrape to avoid redundant work across multiple search queries. Instead of making `already_picked_urls` a global variable or passing it through multiple agents explicitly, `research_agent` *forks* `web_search_agent`. `agent.fork()` creates a new, independent version of the agent for this specific `research_agent` invocation. The `non_freezable_kwargs` argument allows passing mutable objects (like our `set`) that will be shared among all calls *to this forked instance*. TODO mention that this is not the only reason to `fork` ? also not the only reason to pass `non_freezable_kwargs` ?
3.  **Initiating Calls (`initiate_call`):** The `final_answer_agent` will eventually synthesize an answer using all gathered information. We don't have all this information upfront. `final_answer_agent.initiate_call()` creates an `AgentCall` object. This allows `research_agent` to send messages (or message promises) to `final_answer_agent` incrementally using `final_answer_call.send_message()`.
4.  **Parallel Fan-Out (`trigger` without `await`):** For each generated search query, `_web_search_agent.trigger()` is called. Again, no `await` means these sub-agents start working in parallel.
5.  **Out-of-Order Replies (`ctx.reply_out_of_order`):** As results from `_web_search_agent` (which include search and scraping steps) become available, `ctx.reply_out_of_order()` sends them to the output stream of `research_agent`. This is crucial for providing real-time feedback to the user, showing progress from different search branches as it happens, rather than waiting for all searches to complete in a fixed order. TODO the explanation found in a comment in web_research.py is more comprehensive, I think
6.  **Chaining Agent Output:** Finally, `ctx.reply(final_answer_call.reply_sequence())` takes the entire sequence of messages (TODO there will be only one message in the sequence in this particular example) that `final_answer_agent` will produce and appends it to `research_agent`'s own output. `reply_sequence()` also signals to `final_answer_agent` that no more input messages will be sent via `final_answer_call.send_message()`, effectively closing the call.

### The `web_search_agent`: Searching and Selecting Pages

This agent takes a single search query, performs the search, and then uses an LLM to decide which of the resulting pages are most relevant for scraping.

```python
# examples/web_research_tutorial/web_research.py
# ... (research_agent) ...

@miniagent
async def web_search_agent(
    ctx: InteractionContext,
    search_query: str,
    rationale: str,
    already_picked_urls: set[str], # Received from the forked instance
) -> None:
    ctx.reply(f'SEARCHING FOR "{search_query}"\n{rationale}')

    try:
        search_results = await fetch_google_search(search_query) # from utils.py
    except Exception:
        await asyncio.sleep(SLEEP_BEFORE_RETRY_SEC)
        ctx.reply(f"RETRYING SEARCH: {search_query}")
        search_results = await fetch_google_search(search_query)

    ctx.reply(f"SEARCH SUCCESSFUL: {search_query}")

    message_dicts = await aprepare_dicts_for_openai(
        [
            ctx.message_promises, # Original user question
            f"RATIONALE: {rationale}\n\nSEARCH QUERY: {search_query}\n\nSEARCH RESULTS:\n\n{search_results}",
        ],
        system=(
            "This is a user question that another AI agent (not you) will have to answer. Your job, however, is "
            "to list all the web page urls that need to be inspected to collect information related to the "
            "RATIONALE and SEARCH QUERY. SEARCH RESULTS where to take the page urls from are be provided to you as "
            "well. Current date is " + datetime.now().strftime("%Y-%m-%d")
        ),
    )
    response = await openai_client.beta.chat.completions.parse(
        model=SMARTER_MODEL,
        messages=message_dicts,
        response_format=WebPagesToBeRead, # Pydantic model for structured output
    )
    parsed: WebPagesToBeRead = response.choices[0].message.parsed

    web_pages_to_scrape: list[WebPage] = []
    for web_page in parsed.web_pages:
        if web_page.url not in already_picked_urls: # Check against the shared set
            web_pages_to_scrape.append(web_page)
            already_picked_urls.add(web_page.url) # Update the shared set
        if len(web_pages_to_scrape) >= MAX_WEB_PAGES_PER_SEARCH:
            break

    for web_page in web_pages_to_scrape:
        ctx.reply_out_of_order(
            page_scraper_agent.trigger(
                ctx.message_promises, # Original user question
                url=web_page.url,
                rationale=web_page.rationale,
            )
        )

# ... (page_scraper_agent and final_answer_agent)
```

Highlights of `web_search_agent`:
1.  **Actual Web Search:** It calls `fetch_google_search()` (from `utils.py`) to get search results. Includes basic retry logic.
2.  **LLM for Page Selection:** An LLM is prompted to analyze the search results and select promising URLs based on the rationale for the search. The desired output is structured using the `WebPagesToBeRead` Pydantic model.
3.  **Stateful Filtering:** It uses the `already_picked_urls` set (provided by the `fork` in `research_agent`) to avoid re-processing URLs that have already been selected from other search queries in the same overall research task. It also limits the number of pages scraped per search query (`MAX_WEB_PAGES_PER_SEARCH`).
4.  **Parallel Scraping Trigger:** For each selected URL, `page_scraper_agent.trigger()` is called without `await`, initiating parallel scraping operations. Results are again channeled using `ctx.reply_out_of_order()`.

### The `page_scraper_agent`: Fetching and Summarizing Content

This agent is responsible for fetching the content of a single web page and then using an LLM to extract relevant information.

```python
# examples/web_research_tutorial/web_research.py
# ... (web_search_agent) ...

@miniagent
async def page_scraper_agent(
    ctx: InteractionContext,
    url: str,
    rationale: str,
) -> None:
    ctx.reply(f"READING PAGE: {url}\n{rationale}")

    try:
        page_content = await scrape_web_page(url) # from utils.py
    except Exception:
        await asyncio.sleep(SLEEP_BEFORE_RETRY_SEC)
        ctx.reply(f"RETRYING: {url}")
        page_content = await scrape_web_page(url)

    # We await the full summary here because we want to ensure summarization
    # is complete before reporting success for this page.
    page_summary = await OpenAIAgent.trigger(
        [
            ctx.message_promises, # Original user question
            f"URL: {url}\nRATIONALE: {rationale}\n\nWEB PAGE CONTENT:\n\n{page_content}",
        ],
        system=(
            "This is a user question that another AI agent (not you) will have to answer. Your job, however, is "
            "to extract from WEB PAGE CONTENT facts that are relevant to the users original "
            "question. The other AI agent will use the information you extract along with information extracted "
            "by other agents to answer the user's original question later. "
            "Current date is " + datetime.now().strftime("%Y-%m-%d")
        ),
        model=MODEL,
        stream=False, # Streaming isn't critical for this internal summary
        # If summarization fails, let this agent fail rather than sending an error message.
        # This is a choice; for robustness, True might be preferred if partial results are acceptable.
        errors_as_messages=False,
        response_metadata={
            # This summary is for the final_answer_agent, not directly for the user.
            "not_for_user": True,
            # "role": "user", # This metadata might be for other internal tracking
        },
    )
    ctx.reply(f"SCRAPING SUCCESSFUL: {url}")
    ctx.reply(page_summary) # Send the extracted summary

# ... (final_answer_agent)
```

Key points for `page_scraper_agent`:
1.  **Actual Scraping:** It calls `scrape_web_page()` (from `utils.py`), which uses Selenium to get page content. Includes retry logic.
2.  **LLM for Summarization/Extraction:** The MiniAgents built-in `OpenAIAgent` is used here. It's triggered to process the scraped content and extract information relevant to the original user question and the rationale for visiting this specific page.
3.  **Awaiting Specific Results:** Unlike previous `trigger` calls, `page_summary = await OpenAIAgent.trigger(...)` *awaits* the result. This is a design choice: we want to ensure the summarization is complete and successful before this agent reports `SCRAPING SUCCESSFUL` and sends the summary onward.
4.  **Error Handling Choice (`errors_as_messages=False`):** For this particular call to `OpenAIAgent`, `errors_as_messages` is set to `False`. This means if the LLM call fails, the `page_scraper_agent` itself will raise an exception. The overall system is configured with `errors_as_messages=True` (see the `if __name__ == "__main__":` block), so this local override demonstrates fine-grained control. If it were `True` (or defaulted to the global setting), an LLM error would result in an error message being sent as `page_summary` instead of crashing this agent.
5.  **Message Metadata (`response_metadata`):** The `OpenAIAgent.trigger` call includes `response_metadata`. This dictionary is attached to the message(s) produced by `OpenAIAgent`. Here, `"not_for_user": True` signals that this summary is an intermediate result, primarily for the `final_answer_agent`, and shouldn't be directly displayed to the user by the `main` function's loop.

### The `final_answer_agent`: Synthesizing the Result

This agent receives all the summaries and extracted pieces of information from the various `page_scraper_agent` instances and synthesizes a final answer to the user's original question.

```python
# examples/web_research_tutorial/web_research.py
# ... (page_scraper_agent) ...

@miniagent
async def final_answer_agent(ctx: InteractionContext, user_question: Union[Message, tuple[Message, ...]]) -> None:
    # Await all incoming messages (summaries from page_scraper_agents) to ensure
    # they are "materialized" before we proceed to show the "ANSWER" heading. If
    # not for this heading, `await` would not have been important here -
    # OpenAIAgent would have waited for all the incoming messages to make them
    # part of its prompt anyway.
    await ctx.message_promises

    ctx.reply("==========\nANSWER:\n==========")

    ctx.reply(
        OpenAIAgent.trigger(
            [
                "USER QUESTION:",
                user_question, # Passed as a keyword argument during initiate_call
                "INFORMATION FOUND ON THE INTERNET:",
                # Concatenate all received messages (page summaries) into a single text block.
                # `as_single_text_promise()` returns a promise; actual concatenation
                # happens in the background.
                ctx.message_promises.as_single_text_promise(),
            ],
            system=(
                "Please answer the USER QUESTION based on the INFORMATION FOUND ON THE INTERNET. "
                "Current date is " + datetime.now().strftime("%Y-%m-%d")
            ),
            model=MODEL,
            # Streaming can be enabled here for a better user experience if desired
            # stream=True,
            # TODO stream is True by default. did you mean to mention False in the comment ?
        )
    )

# ... (Pydantic models and main block)
```

Key features of `final_answer_agent`:
1.  **Waiting for All Inputs (`await ctx.message_promises`):** Before generating the answer, this agent explicitly `await ctx.message_promises`. This ensures that all the page summaries sent by `research_agent` (via `final_answer_call.send_message()`) have arrived and are resolved. This is important because we want the "ANSWER:" heading to appear *after* all the processing logs (like "SEARCHING...", "READING PAGE...").
2.  **Consolidating Information:** `ctx.message_promises.as_single_text_promise()` is a handy method. It takes the sequence of incoming messages (which are the page summaries) and concatenates them into a single text message promise, with original messages separated by double newlines. This consolidated text, along with the original user question, forms the prompt for the final LLM call.
3.  **Generating Final Answer:** `OpenAIAgent` is triggered one last time to produce the comprehensive answer. Streaming could be enabled here (`stream=True`) if you want the final answer to appear token by token to the user (TODO it already is !).

### Pydantic Models for Structured LLM Output

TODO de-emphasize this, this is not a MiniAgents feature

Throughout the agents, especially when interacting directly with the OpenAI API for specific tasks like query generation or URL selection, Pydantic models are used to define the expected structure of the LLM's response. This is achieved using OpenAI's "Structured Output" feature (via `response_format` in `client.beta.chat.completions.parse`).

```python
# examples/web_research_tutorial/web_research.py
# ... (final_answer_agent) ...

class WebSearch(BaseModel):
    rationale: str
    web_search_query: str


class WebSearchesToBeDone(BaseModel):
    web_searches: tuple[WebSearch, ...]


class WebPage(BaseModel):
    rationale: str
    url: str


class WebPagesToBeRead(BaseModel):
    web_pages: tuple[WebPage, ...]

# ... (if __name__ == "__main__":)
```
These models (`WebSearchesToBeDone`, `WebPagesToBeRead`) help ensure that the LLM provides its output in a way that can be reliably parsed and used by the subsequent logic in the agents.

### Configuring and Running the System

The `if __name__ == "__main__":` block initializes and runs the MiniAgents system:

```python
# examples/web_research_tutorial/web_research.py
# ... (Pydantic models) ...

if __name__ == "__main__":
    MiniAgents(
        # Log LLM requests/responses to markdown files in `llm_logs`
        llm_logger_agent=True,
        # Convert agent errors into messages rather than crashing the agents
        errors_as_messages=True,
        # Optionally include full tracebacks in error messages for debugging
        # error_tracebacks_in_messages=True,
    ).run(main())
```

Key `MiniAgents` configurations used here:
*   **`llm_logger_agent=True`**: This is incredibly useful for debugging. It logs all requests to and responses from LLM agents (like `OpenAIAgent`) into markdown files in an `llm_logs` directory. You can inspect these logs to see the exact prompts, model parameters, and outputs.
*   **`errors_as_messages=True`**: This global setting makes the system more robust. If an agent encounters an unhandled exception, instead of the agent (and potentially the whole flow) crashing, the error is packaged into an `ErrorMessage` object and continues through the system. Downstream agents can then decide how to handle these error messages (e.g., ignore them, try an alternative; TODO this isn't what's happening in our example, though). As we saw, `page_scraper_agent` locally overrides this for one of its LLM calls.
*   **`error_tracebacks_in_messages=True` (commented out)**: If you enable this, the error messages produced when `errors_as_messages=True` will also include the full Python traceback, which can be helpful during development.

## Choosing Your Framework: MiniAgents in Context

# TODO is this section really needed ? isn't it diverting attention from MiniAgents ?

MiniAgents excels when your primary challenge involves managing complex asynchronous data streams and you want to achieve parallel execution of agent tasks with straightforward, procedural-looking code. Its automatic sequence flattening and replayable promises are designed to simplify the development of agents that produce and consume dynamic, streaming information.

However, the AI agent framework landscape is rich, and other tools might be a better fit depending on your project's core needs:

*   If your application demands explicit, graph-based control flow, intricate state management across agent steps, or you need to define complex cyclical interactions (like in sophisticated state machines), a framework like **LangGraph** could be a more direct choice. LangGraph (and the broader Langchain ecosystem) provides strong primitives for these scenarios and boasts a vast array of integrations.
*   For systems centered around multi-agent conversations and dynamic role assignments, frameworks like **AutoGen** offer specialized capabilities.
*   If your focus is on orchestrating role-playing agents in a highly structured collaborative process, **CrewAI** might be more aligned.

Ultimately, the best choice depends on whether your main architectural challenge lies in managing asynchronous data flow and streaming (where MiniAgents shines) or in areas like explicit state/control-flow graphs or leveraging specific collaborative agent paradigms offered by other frameworks.

## Conclusion

This Web Research System demonstrates several powerful features of MiniAgents:
-   **Procedural Code, Parallel Execution:** Agents are written as straightforward async functions, but `trigger` calls without `await` lead to parallel execution.
-   **Promise-Based Communication:** Agents communicate via `MessageSequencePromise` objects, allowing computation to proceed while data is still being gathered.
-   **Sequence Flattening:** Complex, nested calls to agents still result in a single, flat stream of messages for the consumer, managed automatically by the framework.
-   **Flexible Message Handling:** Features like `ctx.reply_out_of_order` and `agent.initiate_call` provide fine-grained control over how and when messages are produced and consumed. TODO is this bullet point really needed ?
-   **State Management with Forks:** `agent.fork()` offers a clean way to create stateful instances of agents for specific tasks without resorting to global state or complex parameter passing. (TODO not only for that ! rewrite this bullet point to de-emphasize the state management aspect ? drop it completely ?
-   **Built-in LLM Integration:** `OpenAIAgent` simplifies interactions with OpenAI models. TODO that's not why OpenAIAgent exists !
-   **Debugging and Robustness:** Features like `llm_logger_agent` and `errors_as_messages` aid in development and create more resilient systems. TODO it is unnatural to group these two features together, they are not related to each other

By focusing on the logic of individual agents, MiniAgents lets you build sophisticated, concurrent AI systems without getting bogged down in the complexities of manual parallelism management.

While frameworks like LangGraph excel at defining the overall control flow and state transitions in an agent graph, and libraries like LlamaIndex provide powerful data indexing and retrieval capabilities, MiniAgents carves out its niche by simplifying the asynchronous data flow and streaming between agents, especially through its automatic sequence flattening and replayable promises. TODO don't position MiniAgents as a replacement for other frameworks, but as a complement to them !
