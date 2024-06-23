

MiniAgents is an asynchronous framework for building language model-based multi-agent systems in Python. It provides a structured way to define, call, and manage agents, making it easier to build complex systems that rely on asynchronous interactions and streaming data.

## Features

- **Agent Management**: Define and manage agents using simple decorators.
- **Asynchronous Interaction**: Support for asynchronous interactions with agents.
- **Streaming**: Stream data token by token or message by message.
- **LLM Integration**: Seamlessly integrate with popular LLMs like OpenAI and Anthropic.
- **Message Handling**: Robust message handling with support for nested messages and promises.
- **Utilities**: A set of utility functions to facilitate common tasks like dialog loops and message joining.
- **Immutable Messages**: Ensures that messages are immutable, making the system more predictable and easier to debug.

## Motivation

The MiniAgents framework was created to address the challenges of building complex, asynchronous, and language model-driven systems. Traditional approaches to agent-based systems often struggle with the complexity of managing multiple agents, handling asynchronous interactions, and integrating with language models.

MiniAgents aims to simplify this process by providing a structured and intuitive way to define agents, manage their interactions, and integrate with language models. The focus on immutable messages and token streaming helps to ensure predictable and efficient system behavior.

## Usage

Here's a simple example of how to define and use an agent with MiniAgents:

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

For more advanced usage, including integrating with OpenAI and Anthropic language models, see the [examples](examples/) directory.

## Installation

You can install MiniAgents using pip:

```
pip install miniagents
```

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

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](LICENSE).
