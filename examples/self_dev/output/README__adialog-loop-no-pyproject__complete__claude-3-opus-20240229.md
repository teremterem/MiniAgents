Here's a suggested README.md for your MiniAgents framework:

# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides abstractions and utilities for defining agents, managing their interactions, and integrating with large language models (LLMs) like OpenAI's GPT and Anthropic's Claude.

## Features

- Define agents as simple Python functions decorated with `@miniagent`
- Chain agents together to create complex interactions and workflows
- Built-in support for OpenAI and Anthropic LLMs
- Manage chat history and persist messages
- Stream LLM responses token-by-token for real-time interactions
- Promises-based architecture for handling asynchronous operations
- Immutable message passing using the `Frozen` class
- Utilities for splitting, joining, and manipulating message sequences

## Installation

To install MiniAgents, use pip:

```
pip install miniagents
```

## Usage

Here's a simple example of defining agents and running them:

```python
from miniagents.miniagents import miniagent, MiniAgents, InteractionContext

@miniagent
async def hello_agent(ctx: InteractionContext) -> None:
    ctx.reply("Hello!")

@miniagent
async def world_agent(ctx: InteractionContext) -> None:
    ctx.reply("World!")

async def amain() -> None:
    async with MiniAgents():
        hello_agent.inquire()
        world_agent.inquire()

if __name__ == "__main__":
    MiniAgents().run(amain())
```

For more examples, see the `examples/` directory.

## Documentation

For detailed documentation on using MiniAgents, see the [docs](docs/).

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MiniAgents is open-source under the [MIT License](LICENSE).
