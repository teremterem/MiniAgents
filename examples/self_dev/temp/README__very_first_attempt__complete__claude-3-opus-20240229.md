# MiniAgents

MiniAgents is a Python framework for building multi-agent systems and integrating large language models (LLMs) into them. It provides a simple and intuitive way to define agents, chain them together, and facilitate communication between them using message passing.

## Key Features

- Define agents as simple Python functions decorated with `@miniagent`
- Chain agents together using the `achain_loop` utility function
- Integrate LLMs from OpenAI and Anthropic as agents
- Stream LLM responses token by token
- Pass messages between agents using the `MessageType` and `MessageSequencePromise` abstractions
- Persist messages using the `on_persist_message` event handler
- Manage the lifecycle of promises and child tasks using the `PromisingContext` class

## Installation

You can install MiniAgents using pip:

```
pip install miniagents
```

## Usage

Here's a simple example of how to define agents and chain them together:

```python
from miniagents.miniagents import miniagent, InteractionContext
from miniagents.utils import achain_loop

@miniagent
async def agent1(ctx: InteractionContext) -> None:
    ctx.reply("Hello from Agent 1!")

@miniagent
async def agent2(ctx: InteractionContext) -> None:
    async for msg in ctx.messages:
        print(f"Agent 2 received: {msg}")
    ctx.reply("Hello from Agent 2!")

async def main() -> None:
    await achain_loop([agent1, agent2])

if __name__ == "__main__":
    from miniagents.miniagents import MiniAgents
    MiniAgents().run(main())
```

For more examples, including how to integrate LLMs, please see the `examples` directory.

## Documentation

Detailed documentation is currently a work in progress. In the meantime, please refer to the docstrings in the source code for information on how to use the various classes and functions provided by MiniAgents.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests on the [GitHub repository](https://github.com/teremterem/MiniAgents).

## License

MiniAgents is released under the MIT License. See `LICENSE` for more information.
