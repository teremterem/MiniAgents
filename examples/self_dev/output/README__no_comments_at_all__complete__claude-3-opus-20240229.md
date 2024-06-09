# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides abstractions and utilities for defining agents, handling messages between agents, and managing agent interactions.

## Features

- Define agents using the `@miniagent` decorator
- Send messages between agents using `MessagePromise` and `MessageSequencePromise`
- Manage agent interactions with the `MiniAgents` context
- Integrate with LLM (Language Model) services like OpenAI and Anthropic
- Utilities for working with messages and sequences, such as `join_messages` and `split_messages`
- Extensible architecture with support for custom message types and agent behaviors

## Installation

You can install MiniAgents using pip:

```
pip install miniagents
```

## Usage

Here's a basic example of how to use MiniAgents:

```python
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext
from miniagents.messages import Message

@miniagent
async def echo_agent(ctx: InteractionContext) -> None:
    async for msg_promise in ctx.messages:
        ctx.reply(await msg_promise)

async def main() -> None:
    async with MiniAgents():
        reply_sequence = echo_agent.inquire("Hello, world!")
        async for reply_promise in reply_sequence:
            print(await reply_promise)

if __name__ == "__main__":
    MiniAgents().run(main())
```

This example defines an `echo_agent` that echoes back any messages it receives. The `main` function sends a message to the agent and prints the reply.

## Documentation

For more detailed documentation and examples, please refer to the [documentation](docs/index.md).

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue on the [GitHub repository](https://github.com/yourusername/MiniAgents). If you'd like to contribute code, please fork the repository and submit a pull request.

## License

MiniAgents is released under the [MIT License](LICENSE).

## Acknowledgements

MiniAgents was inspired by various agent-based frameworks and architectures. We would like to thank the open-source community for their valuable contributions and ideas.
