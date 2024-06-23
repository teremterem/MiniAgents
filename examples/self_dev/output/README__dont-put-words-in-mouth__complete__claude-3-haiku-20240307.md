Here's the improved README.md for the MiniAgents framework:

# MiniAgents

MiniAgents is an asynchronous framework for building multi-agent systems in Python, with a focus on immutable messages and token streaming. It provides a structured way to define, call, and manage agents, making it easier to build complex systems that rely on asynchronous interactions and streaming data.

## Motivation

The MiniAgents framework was created to address the challenges of building agent-based systems that interact with language models (LLMs) and other services. It aims to provide a simple and intuitive way to define agents and their interactions, while also handling the complexities of asynchronous communication, message handling, and token streaming.

The key motivations behind the development of MiniAgents are:

1. **Asynchronous Interaction**: Enabling agents to interact with each other and with external services asynchronously, without blocking the main execution flow.
2. **Streaming**: Allowing agents to process data in a streaming fashion, consuming tokens or messages as they become available, rather than waiting for the entire response.
3. **Immutable Messages**: Ensuring that messages passed between agents are immutable, making the system more predictable and easier to debug.
4. **Modular Design**: Providing a modular and extensible architecture that allows for easy integration with various LLM providers and other external services.
5. **Ease of Use**: Offering a simple and intuitive API for defining and managing agents, making it accessible to developers of all skill levels.

## Features

- **Agent Management**: Define and manage agents using simple decorators.
- **Chat History**: Flexible chat history management, including in-memory and Markdown-based persistence.
- **Asynchronous Interaction**: Support for asynchronous interactions with agents.
- **Streaming**: Stream data token by token or message by message.
- **LLM Integration**: Seamlessly integrate with popular LLMs like OpenAI and Anthropic.
- **Message Handling**: Robust message handling with support for nested messages and promises.
- **Utilities**: A set of utility functions to facilitate common tasks like dialog loops and message joining.
- **Immutable Messages**: Ensures that messages are immutable, making the system more predictable and easier to debug.

## Installation

You can install MiniAgents using pip:

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

if __name__ == "__main__":
    MiniAgents().run(main())
```

For more advanced usage, including integration with LLMs, please refer to the [examples](examples/) directory.

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

Contributions to the MiniAgents framework are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute.

## License

MiniAgents is released under the [MIT License](LICENSE).
