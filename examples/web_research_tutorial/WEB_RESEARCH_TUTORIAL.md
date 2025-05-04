# MiniAgents: Multi-Agent AI With Procedural Simplicity

![MiniAgents on the Moon](images/miniagents-5-by-4-fixed.jpeg)

An open-source, async-first Python framework for building multi-agent AI systems with an innovative approach to parallelism, so you can focus on creating intelligent agents, not on managing the concurrency of your flows.

To install MiniAgents run the following command:

```bash
pip install -U miniagents
```

The source code of the project is hosted on [GitHub](https://github.com/teremterem/MiniAgents). There you can also learn more about it from its [README](https://github.com/teremterem/MiniAgents/blob/main/README.md) file.

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

# Let's build an example web research system with MiniAgents

In this tutorial, we'll build a web research system that can:

1. Break down a user's question into search queries
2. Execute searches in parallel
3. Analyze the search results to identify relevant web pages
4. Scrape and extract information from those pages
5. Synthesize a comprehensive answer

***NOTE: The complete example is available [here](https://github.com/teremterem/WebResearch).***

## Step 1: Environment Setup

First, install MiniAgents and the required dependencies:

```bash
pip install -U miniagents openai httpx pydantic markdownify python-dotenv selenium
```

For LLM we will use [OpenAI](https://platform.openai.com/) and for the google searches as well as scraping we will use [BrightData](https://brightdata.com/), a pay as you go scraping service with two products that we are interested in: [SERP API](https://brightdata.com/products/serp-api) and [Scraping Browser](https://brightdata.com/products/scraping-browser).

Create a `.env` file with your API credentials:

```
OPENAI_API_KEY=your_openai_api_key
BRIGHTDATA_SERP_API_CREDS=username:password
BRIGHTDATA_SCRAPING_BROWSER_CREDS=username:password
```

***ATTENTION: The credentials above are NOT for your whole BrightData account. They are for the SERP API and Scraping Browser respectively (they web site will guide you how to set up both products).***

## Step 2: Basic Structure

Let's create our `web_research.py` file with imports and basic setup:

```python
import asyncio
from datetime import datetime
import random
import os
from typing import Any

from dotenv import load_dotenv
import httpx
from markdownify import markdownify as md
from miniagents import InteractionContext, MiniAgents, miniagent
from miniagents.ext.llms import OpenAIAgent, aprepare_dicts_for_openai
from openai import AsyncOpenAI
from pydantic import BaseModel
from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection

load_dotenv()

BRIGHTDATA_SERP_API_CREDS = os.environ["BRIGHTDATA_SERP_API_CREDS"]
BRIGHTDATA_SCRAPING_BROWSER_CREDS = os.environ["BRIGHTDATA_SCRAPING_BROWSER_CREDS"]

openai_client = AsyncOpenAI()
openai_agent = OpenAIAgent.fork(mutable_state={"async_client": openai_client})
```

## Step 3: Define Data Models

We'll define Pydantic models that we will use to get [structured output](https://platform.openai.com/docs/guides/structured-outputs) from OpenAI:

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

## Step 4: Create the Main Research Agent

Now we'll create our primary research agent that coordinates the entire workflow:

```python
@miniagent
async def research_agent(ctx: InteractionContext) -> None:
    # First, analyze the user's question and break it down into search queries
    messages = await aprepare_dicts_for_openai(
        ctx.message_promises,
        system=(
            "Your job is to breakdown the user's question into a list of web searches that need to be done to answer "
            "the question. Current date is " + datetime.now().strftime("%Y-%m-%d")
        ),
    )
    response = await openai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        response_format=WebSearchesToBeDone,
    )
    parsed: WebSearchesToBeDone = response.choices[0].message.parsed

    collected_web_information = []

    # For each identified search query, trigger a web search (in parallel)
    for web_search in parsed.web_searches:
        ctx.reply(f"> {web_search.rationale}\nSEARCHING FOR: {web_search.web_search_query}")
        collected_web_information.append(
            web_search_agent.trigger(
                ctx.message_promises,
                search_query=web_search.web_search_query,
                rationale=web_search.rationale,
            )
        )

    # Synthesize the final answer based on all collected information
    ctx.reply(
        openai_agent.trigger(
            [
                "USER QUESTION:",
                ctx.message_promises,
                "INFORMATION FOUND ON THE INTERNET:",
                collected_web_information,
            ],
            system=(
                "Please answer the USER QUESTION based on the INFORMATION FOUND ON THE INTERNET. "
                "Current date is " + datetime.now().strftime("%Y-%m-%d")
            ),
            model="gpt-4o",
        )
    )
```

## Step 5: Create the Web Search Agent

Now let's create an agent to handle the web search part:

```python
@miniagent
async def web_search_agent(ctx: InteractionContext, search_query: str, rationale: str) -> None:
    # Execute the search query
    search_results = await fetch_google_search(search_query)

    # Analyze search results to identify relevant web pages
    messages = await aprepare_dicts_for_openai(
        [
            ctx.message_promises,
            f"RATIONALE: {rationale}\n\nSEARCH QUERY: {search_query}\n\nSEARCH RESULTS:\n\n{search_results}",
        ],
        system=(
            "This is a user question that another AI agent (not you) will have to answer. Your job, however, is to "
            "list all the web page urls that need to be inspected to collect information related to the "
            "RATIONALE and SEARCH QUERY. SEARCH RESULTS where to take the page urls from are be provided to you as "
            "well. Current date is " + datetime.now().strftime("%Y-%m-%d")
        ),
    )
    response = await openai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        response_format=WebPagesToBeRead,
    )
    parsed: WebPagesToBeRead = response.choices[0].message.parsed

    web_scraping_results = []

    # For each identified web page, trigger scraping (in parallel)
    for web_page in parsed.web_pages:
        ctx.reply(f"> {web_page.rationale}\nREADING PAGE: {web_page.url}")
        web_scraping_results.append(
            page_scraper_agent.trigger(
                ctx.message_promises,
                url=web_page.url,
                rationale=web_page.rationale,
            )
        )

    # Return all scraping results
    ctx.reply(web_scraping_results)
```

## Step 6: Create the Page Scraper Agent

Now let's implement the agent that will scrape and analyze web pages:

```python
@miniagent
async def page_scraper_agent(ctx: InteractionContext, url: str, rationale: str) -> None:
    # Scrape the web page
    page_content = await asyncio.to_thread(scrape_web_page, url)

    ctx.reply(f"URL: {url}\nRATIONALE: {rationale}")

    # Extract relevant information from the page content
    ctx.reply(
        openai_agent.trigger(
            [
                ctx.message_promises,
                f"URL: {url}\nRATIONALE: {rationale}\n\nWEB PAGE CONTENT:\n\n{page_content}",
            ],
            system=(
                "This is a user question that another AI agent (not you) will have to answer. Your job, however, is "
                "to extract from WEB PAGE CONTENT facts that are relevant to the users original "
                "question. The other AI agent will use the information you extract along with information extracted "
                "by other agents to answer the user's original question later. "
                "Current date is " + datetime.now().strftime("%Y-%m-%d")
            ),
            model="gpt-4o",
        )
    )
```

## Step 7: Add Utility Functions

Let's implement the utility functions for web searching and scraping:

```python
async def fetch_google_search(query: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(
            proxy=f"https://{BRIGHTDATA_SERP_API_CREDS}@brd.superproxy.io:33335", verify=False, timeout=30
        ) as client:
            response = await client.get(f"https://www.google.com/search?q={query}&brd_json=1")
        return response.json()
    except Exception as e:
        return f"FAILED TO SEARCH FOR: {query}\n{e}"


def scrape_web_page(url: str) -> str:
    try:
        sbr_connection = ChromiumRemoteConnection(
            f"https://{BRIGHTDATA_SCRAPING_BROWSER_CREDS}@brd.superproxy.io:9515",
            "goog",
            "chrome",
        )
        with Remote(sbr_connection, options=ChromeOptions()) as driver:
            driver.get(url)
            html = driver.page_source
        return md(html)
    except Exception as e:
        return f"FAILED TO READ WEB PAGE: {url}\n{e}"
```

## Step 8: Create the Main Function

Finally, let's create the main function to tie everything together:

```python
async def main():
    question = input("Enter your question: ")

    response_promises = research_agent.trigger(question)

    print("\nResearching...\n")
    async for message_promise in response_promises:
        async for token in message_promise:
            print(token, end="", flush=True)
        print("\n")


if __name__ == "__main__":
    MiniAgents(llm_logger_agent=True).run(main())
```

## Running the Research System

Now you can run your web research system:

```bash
python web_research.py
```

Enter a complex question like:
```
I'm thinking of moving from Lviv to Kyiv — what should I know about the cost of living, neighborhoods, gyms, and, most importantly, finding an apartment if I have two cats?
```

## How This Showcases MiniAgents' Power

This web research system demonstrates two key strengths of MiniAgents:

### 1. Message Sequence Promises

Every interaction between agents happens through message sequence promises:
- `web_search_agent.trigger()` returns promises, not actual results
- When we append to `collected_web_information`, we're appending promises
- The final synthesis waits for the promises to be resolved (at this point we finally need those messages)

### 2. Non-blocking Parallelism

The system exhibits incredible parallelism with no special code:
- Multiple search queries are processed simultaneously
- Multiple web pages are scraped in parallel
- All without explicit thread or process management

This happens because MiniAgents uses the `start_soon` mode by default, allowing each agent to run in the background. The immutable message design ensures this parallelism is safe and efficient.

The system naturally parallelizes IO-bound tasks without explicit concurrency code (AI agents are usually IO-bound, because language models, no matter cloud or local, are usually hosted outside of the agentic process).

### P. S. Here is sample output from the Web Search application that we just built in this tutorial:

```
Enter your question: I'm thinking of moving from Lviv to Kyiv — what should I know about the cost of living, neighborhoods, gyms, and, most importantly, finding an apartment if I have two cats?


Researching...

> Determine if the cost of living in Kyiv is higher or lower compared to Lviv, considering factors like housing, groceries, and other expenses.
SEARCHING FOR: Kyiv vs Lviv cost of living 2025

> Identify the best neighborhoods in Kyiv for expats and families that are also pet-friendly, as the user owns two cats.
SEARCHING FOR: Best neighborhoods in Kyiv for expats with pets 2025

> To discover popular gyms in Kyiv, compare membership prices, facilities offered, and proximity to residential areas.
SEARCHING FOR: Best gyms in Kyiv membership cost and offers 2025

> Find out the process and best platforms to use when looking for apartments in Kyiv that accommodate pet owners.
SEARCHING FOR: How to find a pet-friendly apartment in Kyiv 2025

> Explore potential challenges and solutions when relocating with pets to ensure a smooth transition for the user's cats.
SEARCHING FOR: Moving to Kyiv with cats tips 2025

> Gather insights on the overall lifestyle in Kyiv, making the transition easier by understanding local culture, transportation, and amenities.
SEARCHING FOR: Living in Kyiv expat guide 2025


Considering the available information about moving from Lviv to Kyiv, here’s a detailed overview of key factors you'll want to consider:

### Cost of Living:
- **General Costs**: Kyiv generally has a higher cost of living than Lviv. Renting prices, utilities, and groceries are more expensive. You might expect to pay 69% more for housing and 84% more for food in Kyiv compared to Lviv.
- **Rent**: Renting a one-bedroom apartment in Kyiv ranges from $500 to $700 in the city center. Outside of the city center, it costs between $400 and $500. If you require a bit more space, a two-bedroom apartment could be up to $1,000 per month. You will also need to factor in higher utility costs, which tend to be about 33% higher than in Lviv.

### Neighborhoods:
- **Popular Areas**: Central districts such as Shevchenkivskyi and Pecherskyi are vibrant with historical, cultural, and leisure attractions, though they come with a higher rental price tag. Expat-friendly neighborhoods like Podil and Obolon provide a balance between cost and accessibility to amenities. For advice on neighborhoods, tourists and expats might consult resources like Airbnb reviews or local real estate forums.
- **Pet-Friendly Areas**: It is important to check if your chosen neighborhood and specific building is pet-friendly, especially for keeping two cats. Neighborhoods with green spaces or those near parks could offer more favorable living conditions for pet owners.

### Gyms and Fitness:
- **Gym Memberships**: Monthly gym memberships cost between 1,500 and 3,000 UAH (~$40-$80). Kyiv offers a broad range of fitness centers, from basic gyms to full-service health clubs in both residential and business districts.

### Finding an Apartment with Two Cats:
- **Pet Policies**: Not all apartments will be pet-friendly. It's crucial to verify each potential property’s rules regarding pets, specifically cats, as policies and extra charges (such as a pet deposit or pet rent) vary by landlord. Pet-friendly accommodations might be searchable on platforms like Airbnb or through targeted searches in expat forums.
- **Resources**: Use platforms like OLX, LUN, and local Facebook groups such as "Kiev Apartments" to find current listings. Consulting with a local real estate agent to aid in finding pet-friendly rentals could also be beneficial.

### Additional Considerations:
- **Transportation**: Public transport is reasonably priced, and areas closer to metro stations may prove convenient for daily commuting.
- **Safety and Environment**: While Kyiv is a bustling city with vibrant cultural activities, ongoing regional tensions might affect perceptions of safety, a crucial factor to account for in your plans.

### Moving with Cats:
- **Regulations and Care**: Make sure your cats have valid microchips and vaccinations, as these are required for relocation. Meanwhile, preparing them for the move by crate training and slowly introducing them to the new living space in Kyiv upon arrival will help them adapt smoothly.

Being aware of these factors will help in creating a more defined relocation plan as you transition from Lviv to Kyiv with your two cats.
```

Thanks!
