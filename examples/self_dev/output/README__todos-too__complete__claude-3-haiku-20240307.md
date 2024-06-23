

MiniAgents is an asynchronous framework for building multi-agent systems in Python, with a focus on immutable messages and token streaming. It provides a structured way to define, call, and manage agents, making it easier to build complex systems that rely on asynchronous interactions and streaming data.

## Why MiniAgents?

The MiniAgents framework was created to address the challenges of building complex, multi-agent systems that interact with language models (LLMs) and other services. It aims to provide a simple and intuitive way to define agents and their interactions, while also handling the complexities of asynchronous communication, message handling, and token streaming.

The key motivations behind the development of MiniAgents are:

1. **Asynchronous Interaction**: MiniAgents is designed to facilitate asynchronous interactions between agents, allowing for efficient and non-blocking communication.
2. **Token Streaming**: The framework supports streaming of messages and tokens, enabling efficient processing of large amounts of data.
3. **Immutable Messages**: MiniAgents ensures that messages are immutable, making the system more predictable and easier to debug.
4. **Modular Design**: The framework is designed to be modular, allowing for easy integration with various LLM providers and other services.
5. **Ease of Use**: MiniAgents aims to provide a simple and intuitive API for defining and managing agents, making it accessible to a wide range of developers.

## Features

- **Agent Management**: Define and manage agents using simple decorators.
- **Chat History**: Flexible chat history management, including in-memory and Markdown-based persistence.
- **Asynchronous Interaction**: Support for asynchronous interactions with agents.
- **Streaming**: Stream data token by token or message by message.
- **LLM Integration**: Seamless integration with popular LLMs like OpenAI and Anthropic.
- **Message Handling**: Robust message handling with support for nested messages and promises.
- **Utilities**: A set of utility functions to facilitate common tasks like dialog loops and message joining.
- **Immutable Messages**: Ensures that messages are immutable, making the system more predictable and easier to debug.

## Installation

To install MiniAgents, use pip:

```bash
pip install miniagents
```

## Usage

Here's a simple example of how to define and use an agent in MiniAgents:

```python
from miniagents import miniagent, InteractionContext, MiniAgents

@miniagent
async def my_agent(ctx: InteractionContext):
    async for message in ctx.messages:
        ctx.reply(f"You said: {message}")

async def main():
    async with MiniAgents():
        reply = await my_agent.inquire("Hello!")
        print(reply)  # prints "You said: Hello!"

asyncio.run(main())
```

For more advanced usage, including integration with LLMs, see the [examples](examples/) directory.

## Documentation

The MiniAgents framework is organized into several modules:

- `miniagents.miniagents`: Core classes for creating and managing agents
- `miniagents.messages`: Classes for representing and handling messages
- `miniagents.promising`: Utilities for managing asynchronous operations using promises
- `miniagents.ext`: Extensions for integrating with external services and utilities
    - `miniagents.ext.chat_history_md`: Chat history management using Markdown files
    - `miniagents.ext.console_user_agent`: User agent for interacting via the console
    - `miniagents.ext.llm`: Integration with language models
        - `miniagents.ext.llm.openai`: OpenAI language model integration
        - `miniagents.ext.llm.anthropic`: Anthropic language model integration

For detailed documentation on each module and class, please refer to the docstrings in the source code.

## Contributing

Contributions to MiniAgents are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute.

## License

MiniAgents is released under the [MIT License](LICENSE).
