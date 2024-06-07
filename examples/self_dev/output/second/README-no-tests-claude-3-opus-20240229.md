Here's a README.md for your MiniAgents framework:

# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides a simple and flexible way to define agents, chain them together, and manage their interactions.

## Features

- Define agents as simple Python functions decorated with `@miniagent`
- Chain agents together using the `achain_loop` utility function
- Stream messages between agents using the `MessageSequence` and `MessageSequencePromise` classes
- Integrate with large language models (LLMs) like OpenAI's GPT and Anthropic's Claude
- Manage the lifecycle of promises using the `PromisingContext` class
- Serialize and deserialize messages using the `Frozen` class
- Split and join messages using the `split_messages` and `join_messages` utility functions

## Installation

You can install MiniAgents using Poetry:

```bash
poetry add miniagents
```

## Usage

Here's a simple example of how to use MiniAgents:

```python
from miniagents import miniagent, achain_loop, AWAIT

@miniagent
async def user_agent(ctx):
    async for msg in ctx.messages:
        print(f"User: {msg}")
    ctx.reply("Hello, how can I assist you today?")

@miniagent
async def assistant_agent(ctx):
    async for msg in ctx.messages:
        print(f"Assistant: {msg}")
    ctx.reply("I'm doing well, thanks for asking!")

async def main():
    await achain_loop([
        user_agent,
        AWAIT,
        assistant_agent,
    ])

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

This example defines two agents, `user_agent` and `assistant_agent`, and chains them together using the `achain_loop` utility function. The `AWAIT` sentinel is used to indicate that the loop should wait for the previous agent to finish before proceeding to the next one.

## Documentation

For more detailed documentation, please refer to the docstrings in the source code.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## License

MiniAgents is released under the MIT License. See the `LICENSE` file for more details.
