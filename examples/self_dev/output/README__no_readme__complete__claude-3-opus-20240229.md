# MiniAgents

MiniAgents is a Python framework for building composable AI agents. It provides abstractions and utilities for defining agents, passing messages between them, and orchestrating their interactions.

## Key Features

- Define agents as simple async Python functions decorated with `@miniagent`
- Agents communicate by passing messages via an `InteractionContext`
- Agents can be composed together into agent chains and networks
- Built-in support for integrating LLMs like OpenAI and Anthropic models as agents
- Stream tokens from LLMs and messages between agents
- Persist agent interactions by hooking into message events
- `Promise`-based programming model for managing asynchronous message flows

## Installation

Install from PyPI:

```
pip install miniagents
```

## Basic Usage

Here's a simple example of defining two agents that interact:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def agent1(ctx: InteractionContext) -> None:
    ctx.reply("Hello from Agent 1!")

@miniagent
async def agent2(ctx: InteractionContext) -> None:
    async for msg in ctx.messages:
        print(f"Agent 2 received: {msg}")
        ctx.reply(f"Agent 2 says: {msg}")

agent1.inquire(agent2.inquire())
```

This will print:
```
Agent 2 received: Hello from Agent 1!
Agent 2 says: Hello from Agent 1!
```

## Integrating LLMs

MiniAgents provides wrappers for easily integrating LLMs as agents:

```python
from miniagents.ext.llm.openai import create_openai_agent

llm_agent = create_openai_agent(model="gpt-3.5-turbo")

reply = llm_agent.inquire("What is the capital of France?")
print(reply) # Prints: The capital of France is Paris.
```

## Documentation

For more details on using MiniAgents, see the full documentation at https://miniagents.readthedocs.io/

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md for guidelines.

## License

MiniAgents is open-source under the MIT License. See LICENSE for more details.
