# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides a set of tools and abstractions for defining agents, managing their interactions, and integrating with language models (LLMs) such as OpenAI's GPT and Anthropic's Claude.

## Key Features

- Define agents as simple Python functions decorated with `@miniagent`
- Agents can send and receive messages asynchronously
- Built-in support for OpenAI and Anthropic LLMs
- Stream tokens from LLMs piece-by-piece
- Promises and async iterators used extensively to enable non-blocking execution
- Immutable message passing via `Frozen` pydantic models
- Automatic hashing of messages for deduplication
- Hooks to persist messages as they are sent/received
- Utilities for joining, splitting, chaining agent interactions

## Installation

Install from PyPI using pip:

```
pip install miniagents
```

## Basic Usage

Here's a simple example of defining two agents that interact:

```python
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext

@miniagent
async def agent1(ctx: InteractionContext) -> None:
    ctx.reply("Hello from Agent 1!")

@miniagent
async def agent2(ctx: InteractionContext) -> None:
    async for msg in ctx.messages:
        print(f"Agent 2 received: {msg}")
        ctx.reply(f"Agent 2 says: {msg.text}")

async def main():
    async with MiniAgents():
        agent2.inquire(agent1.inquire())

asyncio.run(main())
```

This will output:
```
Agent 2 received: Hello from Agent 1!
```

## Integrating LLMs

MiniAgents provides wrappers to easily integrate LLMs as agents:

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent(model="gpt-3.5-turbo")

async def main():
    async with MiniAgents():
        print(await openai_agent.inquire("Tell me a joke"))

asyncio.run(main())
```

## Documentation

For more details on using MiniAgents, please see the full documentation.

## Contributing

Contributions are welcome! Please see the contributing guide for details.

## License

MiniAgents is open-source under the MIT license.
