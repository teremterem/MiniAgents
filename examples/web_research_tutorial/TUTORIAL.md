# MiniAgents: Multi-Agent AI With Procedural Simplicity

![MiniAgents on the Moon](../../images/banner-miniagents-2025-04-27.jpeg)

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

# In this tutorial we'll build an example web research system with MiniAgents

In this tutorial, we'll build a web research system that can:

1. Break down a user's question into search queries
2. Execute searches in parallel
3. Analyze the search results to identify relevant web pages
4. Scrape and extract information from those pages
5. Synthesize a comprehensive answer

***NOTE: The complete example is available [here](https://github.com/teremterem/MiniAgents/tree/main/examples/web_research_tutorial).***

## Let's start by exploring the framework's central feature: Sequence Flattening
