# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides a simple and flexible way to define agents and their interactions.

## Features

- Define agents as simple Python functions decorated with `@miniagent`
- Agents can send and receive messages asynchronously
- Agents can be composed into hierarchical structures
- Agents can be run in parallel or sequentially
- Built-in support for integrating with OpenAI and Anthropic language models
- Extensible architecture for adding new types of agents and message handlers

## Installation

You can install MiniAgents using pip:

```bash
pip install miniagents
```

## Usage

Here's a simple example of how to define and run agents using MiniAgents:

```python
from miniagents import miniagent, MiniAgents, InteractionContext

@miniagent
async def hello_agent(ctx: InteractionContext):
    ctx.reply("Hello, world!")

@miniagent
async def echo_agent(ctx: InteractionContext):
    async for msg in ctx.messages:
        ctx.reply(f"You said: {msg}")

async def main():
    async with MiniAgents():
        hello_agent.inquire()
        echo_agent.inquire("How are you?")

if __name__ == "__main__":
    MiniAgents().run(main())
```

This will output:

```
Hello, world!
You said: How are you?
```

## Documentation

For more detailed documentation and examples, please refer to the [docs](docs/) directory.

## Contributing

Contributions are welcome! Please see the [contributing guide](CONTRIBUTING.md) for more information.

## License

MiniAgents is released under the [MIT License](LICENSE).
