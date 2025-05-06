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

### Real Message Sequence Flattening with MiniAgents

Now let's see how MiniAgents handles the same workflow with its "Message Sequence Flattening" capability:

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

1. **Automatic concurrency**: All agents start working in parallel as soon as they're triggered  # TODO mention "task switching"
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

# TODO the third "replay", the one with "global" await should go here
```

MiniAgents uses `reply()` for sequential responses and `reply_out_of_order()` when you want messages delivered as soon as they're available, rather than in strict creation (TODO reply, not creation) order. This gives you control over message ordering while maintaining the benefits of automatic concurrency.

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

Also, as you might have noticed in the animation above, the response sequence can be replayed as many times as needed. Both, message sequence flattening and sequence replayability apply to all sequences, not only response sequences, but also ones that go as input to other agents. TODO mention why replayability is an important feature.

## Web Research System with real operations

Now that we understand the core concept of Message Sequence Flattening, let's build a complete Web Research System using MiniAgents.

### System Architecture

Our Web Research System will have four agents:

1. `research_agent` - The orchestrator that coordinates the entire research process
2. `web_search_agent` - Executes searches and identifies relevant pages
3. `page_scraper_agent` - Extracts information from web pages
4. `final_answer_agent` - Synthesizes findings into a comprehensive answer

Let's implement each agent step by step.

### Setting up the environment

First, we need to import necessary libraries and set up our environment:

```python
import asyncio
from datetime import datetime
from typing import Union

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel

from utils import check_miniagents_version, fetch_google_search, scrape_web_page

from miniagents import AgentCall, InteractionContext, Message, MessageSequencePromise, MiniAgents, miniagent
from miniagents.ext.llms import OpenAIAgent, aprepare_dicts_for_openai

load_dotenv()

MODEL = "gpt-4o-mini"  # or "gpt-4o" for better quality
SMARTER_MODEL = "o4-mini"  # or "o3" for better quality
MAX_WEB_PAGES_PER_SEARCH = 2
```

The `utils.py` module contains helper functions for web searching and scraping, but we don't need to focus on those details. They're available in the GitHub repository if you're interested.

### Defining our data models

TODO these aren't MiniAgents's data models, they're just Pydantic models used for structured output by OpenAI. The title should be changed to deemphasize their importance.

Let's define some Pydantic models that our agents will use to structure their communication:

```python
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
```

### Implementing the research_agent

The `research_agent` is our main orchestrator. It breaks down the user's question into search queries, triggers the web searches, and coordinates the final answer:

```python
@miniagent
async def research_agent(ctx: InteractionContext) -> None:
    ctx.reply("RESEARCHING...")

    # Analyze the user's question and break it down into search queries
    message_dicts = await aprepare_dicts_for_openai(
        ctx.message_promises,
        system=(
            "Your job is to breakdown the user's question into a list of web searches that need to be done to answer "
            "the question. Please try to optimize your search queries so there aren't too many of them. Current date "
            "is " + datetime.now().strftime("%Y-%m-%d")
        ),
    )

    # Use OpenAI's Structured Output feature to get search queries
    response = await openai_client.beta.chat.completions.parse(
        model=SMARTER_MODEL,
        messages=message_dicts,
        response_format=WebSearchesToBeDone,
    )
    parsed: WebSearchesToBeDone = response.choices[0].message.parsed

    ctx.reply(f"RUNNING {len(parsed.web_searches)} WEB SEARCHES")

    # Track URLs we've already scraped to avoid duplicates
    already_picked_urls = set[str]()

    # Fork the web_search_agent to maintain state across calls
    _web_search_agent = web_search_agent.fork(
        non_freezable_kwargs={
            "already_picked_urls": already_picked_urls,
        },
    )

    # Initiate the final answer agent
    final_answer_call: AgentCall = final_answer_agent.initiate_call(
        user_question=await ctx.message_promises,
    )

    # Trigger web searches in parallel
    for web_search in parsed.web_searches:
        search_and_scraping_results = _web_search_agent.trigger(
            ctx.message_promises,
            search_query=web_search.web_search_query,
            rationale=web_search.rationale,
        )
        # Send results to the user as they become available
        ctx.reply_out_of_order(search_and_scraping_results)

        # Send the same results to the final answer agent
        final_answer_call.send_message(search_and_scraping_results)

    # Add the final answer to our response
    ctx.reply(final_answer_call.reply_sequence())
```

Notice how we're using several important MiniAgents features:

1. **Agent forking** with `web_search_agent.fork()` - This creates a modified version of the agent that maintains state (the `already_picked_urls` set) across multiple calls.

2. **Non-blocking operations** with `trigger` - We don't use `await` when calling `trigger`, so all searches start in parallel.

3. **Out-of-order replies** with `reply_out_of_order` - This delivers messages as soon as they're available, rather than waiting for previous operations to complete.

4. **Agent calls** with `initiate_call` and `send_message` - This allows us to incrementally build input for the final answer agent as we collect search results.

### Implementing the web_search_agent

The `web_search_agent` executes search queries and identifies relevant web pages to scrape:

```python
@miniagent
async def web_search_agent(
    ctx: InteractionContext,
    search_query: str,
    rationale: str,
    already_picked_urls: set[str],
) -> None:
    ctx.reply(f'SEARCHING FOR "{search_query}"\n{rationale}')

    try:
        # Execute the search query
        search_results = await fetch_google_search(search_query)
    except Exception:
        # Retry on failure
        await asyncio.sleep(SLEEP_BEFORE_RETRY_SEC)
        ctx.reply(f"RETRYING SEARCH: {search_query}")
        search_results = await fetch_google_search(search_query)

    ctx.reply(f"SEARCH SUCCESSFUL: {search_query}")

    # Analyze search results to identify relevant web pages
    message_dicts = await aprepare_dicts_for_openai(
        [
            ctx.message_promises,
            f"RATIONALE: {rationale}\n\nSEARCH QUERY: {search_query}\n\nSEARCH RESULTS:\n\n{search_results}",
        ],
        system=(
            "This is a user question that another AI agent (not you) will have to answer. Your job is to "
            "list all the web page urls that need to be inspected to collect information related to the "
            "RATIONALE and SEARCH QUERY. SEARCH RESULTS where to take the page urls from are provided to you as "
            "well. Current date is " + datetime.now().strftime("%Y-%m-%d")
        ),
    )

    response = await openai_client.beta.chat.completions.parse(
        model=SMARTER_MODEL,
        messages=message_dicts,
        response_format=WebPagesToBeRead,
    )
    parsed: WebPagesToBeRead = response.choices[0].message.parsed

    # Filter out pages we've already scraped and limit the total number
    web_pages_to_scrape: list[WebPage] = []
    for web_page in parsed.web_pages:
        if web_page.url not in already_picked_urls:
            web_pages_to_scrape.append(web_page)
            already_picked_urls.add(web_page.url)
        if len(web_pages_to_scrape) >= MAX_WEB_PAGES_PER_SEARCH:
            break

    # Trigger scraping for each page in parallel
    for web_page in web_pages_to_scrape:
        ctx.reply_out_of_order(
            page_scraper_agent.trigger(
                ctx.message_promises,
                url=web_page.url,
                rationale=web_page.rationale,
            )
        )
```

This agent demonstrates two more important concepts:

1. **State management** - It receives and updates the `already_picked_urls` set to avoid duplicate scraping.
2. **Error handling** - It includes retry logic for failed searches.

### Implementing the page_scraper_agent

The `page_scraper_agent` scrapes web pages and extracts relevant information:

```python
@miniagent
async def page_scraper_agent(
    ctx: InteractionContext,
    url: str,
    rationale: str,
) -> None:
    ctx.reply(f"READING PAGE: {url}\n{rationale}")

    try:
        # Scrape the web page
        page_content = await scrape_web_page(url)
    except Exception:
        # Retry on failure
        await asyncio.sleep(SLEEP_BEFORE_RETRY_SEC)
        ctx.reply(f"RETRYING: {url}")
        page_content = await scrape_web_page(url)

    # Extract relevant information using OpenAI
    page_summary = await OpenAIAgent.trigger(
        [
            ctx.message_promises,
            f"URL: {url}\nRATIONALE: {rationale}\n\nWEB PAGE CONTENT:\n\n{page_content}",
        ],
        system=(
            "This is a user question that another AI agent (not you) will have to answer. Your job is "
            "to extract from WEB PAGE CONTENT facts that are relevant to the users original "
            "question. The other AI agent will use the information you extract along with information extracted "
            "by other agents to answer the user's original question later. "
            "Current date is " + datetime.now().strftime("%Y-%m-%d")
        ),
        model=MODEL,
        stream=False,
        errors_as_messages=False,
        response_metadata={
            "not_for_user": True,
            "role": "user",
        },
    )

    ctx.reply(f"SCRAPING SUCCESSFUL: {url}")
    ctx.reply(page_summary)
```

Here we see the use of the built-in `OpenAIAgent` for LLM-powered information extraction. The `response_metadata` parameter with `"not_for_user": True` indicates that this message should not be shown to the end user.

### Implementing the final_answer_agent

The `final_answer_agent` synthesizes all the gathered information into a comprehensive answer:

```python
@miniagent
async def final_answer_agent(ctx: InteractionContext, user_question: Union[Message, tuple[Message, ...]]) -> None:
    # Wait for all input messages to be available before sending the answer header
    await ctx.message_promises
    ctx.reply("==========\nANSWER:\n==========")

    ctx.reply(
        OpenAIAgent.trigger(
            [
                "USER QUESTION:",
                user_question,
                "INFORMATION FOUND ON THE INTERNET:",
                ctx.message_promises.as_single_text_promise(),
            ],
            system=(
                "Please answer the USER QUESTION based on the INFORMATION FOUND ON THE INTERNET. "
                "Current date is " + datetime.now().strftime("%Y-%m-%d")
            ),
            model=MODEL,
        )
    )
```

The `await ctx.message_promises` ensures that the "ANSWER" header doesn't appear until all the research is complete. Then we use `as_single_text_promise()` to concatenate all the collected information into a single text that can be used by OpenAI to generate the final answer.

### Running the system

Finally, we need to set up the entry point for our application:

```python
async def main():
    question = input("\nEnter your question: ")

    # Trigger the main agent (non-blocking)
    response_promises: MessageSequencePromise = research_agent.trigger(question)

    print()
    # Iterate over message promises and display them to the user
    async for message_promise in response_promises:
        # Skip messages not intended for the user
        if message_promise.known_beforehand.get("not_for_user"):
            continue

        # Stream tokens for a smoother experience
        async for token in message_promise:
            print(token, end="", flush=True)
        print("\n")

if __name__ == "__main__":
    MiniAgents(
        llm_logger_agent=True,  # Log LLM requests and responses as markdown
        errors_as_messages=True,  # Handle errors gracefully
    ).run(main())
```

Note the important configuration in the `MiniAgents` constructor:
- `llm_logger_agent=True` logs LLM requests and responses for debugging
- `errors_as_messages=True` makes the system robust by treating errors as messages rather than crashing

### Key MiniAgents features demonstrated

This Web Research System demonstrates several powerful features of MiniAgents:

1. **Parallel execution** with non-blocking agent calls
2. **Message sequence flattening** for working with nested agent calls
3. **State management** through agent forking
4. **Error handling** with retry logic and errors as messages
5. **Flexible message delivery** with out-of-order replies
6. **Incremental agent calls** with `initiate_call` and `send_message`
7. **Message metadata** to control display behavior

## Conclusion

You've now built a complete Web Research System using MiniAgents! The system demonstrates how to write procedural code that executes in parallel, how to manage agent state, and how to coordinate multiple agents working together.

The full code is available in the [GitHub repository](https://github.com/teremterem/MiniAgents/tree/main/examples/web_research_tutorial).
