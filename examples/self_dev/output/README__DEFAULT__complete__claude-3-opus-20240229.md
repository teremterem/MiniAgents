

MiniAgents is an asynchronous Python framework for building multi-agent systems that interact with large language models (LLMs) and other services. It provides a structured way to define, call, and manage agents, making it easier to build complex systems that rely on asynchronous interactions and streaming data.

## Features

- **Agent Management**: Easily create, manage, and chain multiple agents using simple decorators.
- **Chat History**: Manage chat history with support for in-memory and markdown file storage.
- **Asynchronous Interaction**: Support for asynchronous interactions between agents.
- **LLM Integration**: Seamlessly integrate with popular LLMs like OpenAI and Anthropic.
- **Message Handling**: Robust message handling with support for nested messages and promises.
- **Streaming**: Stream data token by token or message by message for efficient processing.
- **Utilities**: A set of utility functions to facilitate common tasks like dialog loops and agent chaining.
- **Immutable Messages**: Ensures that messages are immutable, making the system more predictable and easier to debug.

## Installation

```bash
pip install miniagents
```

## Basic Usage

Here's a simple example of using MiniAgents to create a dialog between a user and an AI assistant powered by OpenAI's GPT-3.5-turbo model:

```python
from miniagents.ext.llm.openai import openai_agent
from miniagents.ext.console_user_agent import console_user_agent
from miniagents.utils import adialog_loop

async def main():
    assistant_agent = openai_agent.fork(model="gpt-3.5-turbo")
    await adialog_loop(console_user_agent, assistant_agent)

asyncio.run(main())
```

This will start an interactive dialog where the user can chat with the AI assistant in the console.

## Documentation

The framework is organized into several modules:

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

### Core Concepts

- **MiniAgents**: The main class that manages the lifecycle of agents and their interactions.
- **MiniAgent**: A wrapper for an agent function that allows calling the agent.
- **InteractionContext**: Provides context for the interaction, including the messages and the agent.
- **Message**: Represents a message that can be sent between agents.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](LICENSE).

---

Happy coding with MiniAgents! 🚀
