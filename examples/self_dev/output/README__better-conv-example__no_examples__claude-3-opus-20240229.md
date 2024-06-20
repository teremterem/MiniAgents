# MiniAgents

MiniAgents is an asynchronous framework for building LLM-based multi-agent systems in Python, with a focus on immutable messages and token streaming.

## Features

- Asynchronous execution of agents
- Immutable messages for communication between agents
- Token streaming for efficient processing of large messages
- Integration with popular LLM providers (OpenAI, Anthropic)
- Flexible agent composition and chaining
- Extensible architecture for custom agents and message types

## Installation

You can install MiniAgents using pip:

```bash
pip install miniagents
```

## Usage

Here's a simple example of how to use MiniAgents to create and run agents:

```python
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext
from miniagents.messages import Message

@miniagent
async def hello_agent(ctx: InteractionContext) -> None:
    ctx.reply(Message(text="Hello, world!"))

async def main():
    async with MiniAgents():
        reply_sequence = hello_agent.inquire()
        async for msg_promise in reply_sequence:
            print(await msg_promise)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

This example defines a simple agent using the `@miniagent` decorator, which replies with a "Hello, world!" message. The `main` function creates a `MiniAgents` context, inquires the agent, and prints the reply messages.

For more advanced usage, including agent chaining, custom message types, and integration with LLM providers, please refer to the documentation and examples.

## Documentation

The full documentation for MiniAgents is available at [https://miniagents.readthedocs.io/](https://miniagents.readthedocs.io/).

## Contributing

Contributions to MiniAgents are welcome! If you find a bug, have a feature request, or want to contribute code, please open an issue or submit a pull request on the [GitHub repository](https://github.com/teremterem/MiniAgents).

## License

MiniAgents is released under the [MIT License](https://opensource.org/licenses/MIT).
