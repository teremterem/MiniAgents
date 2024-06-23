Here's the improved README.md for the MiniAgents framework:

# MiniAgents

MiniAgents is an asynchronous Python framework for building agent-based systems that interact with language models (LLMs) and other services. It provides a structured way to define, call, and manage agents, making it easier to build complex systems that rely on asynchronous interactions and streaming data.

## Motivation

The MiniAgents framework was created to address the challenges of building multi-agent systems that leverage language models. Specifically, it aims to:

1. **Simplify Agent Management**: Provide a simple and intuitive way to define and manage agents, including the ability to chain them together for more complex interactions.
2. **Asynchronous Interaction**: Support asynchronous interactions between agents, allowing for efficient and non-blocking communication.
3. **Streaming**: Enable streaming of data, both messages and tokens, to optimize the use of language models and other services.
4. **Immutable Messages**: Ensure that messages are immutable, making the system more predictable and easier to debug.
5. **Extensibility**: Provide a flexible and extensible architecture that allows for easy integration with various LLM providers and other services.

## Features

- **Agent Management**: Define and manage agents using simple decorators.
- **Asynchronous Interaction**: Support for asynchronous interactions with agents.
- **Streaming**: Stream data token by token or message by message.
- **Immutable Messages**: Ensures that messages are immutable, making the system more predictable and easier to debug.
- **LLM Integration**: Seamlessly integrate with popular LLMs like OpenAI and Anthropic.
- **Message Handling**: Robust message handling with support for nested messages and promises.
- **Utilities**: A set of utility functions to facilitate common tasks like dialog loops and message joining.

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

## Extending MiniAgents

You can extend the functionality of MiniAgents by creating custom agents, message types, and chat history handlers. The framework is designed to be modular and flexible, allowing you to integrate it with various services and customize its behavior to fit your needs.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](LICENSE).
