

MiniAgents is an asynchronous Python framework for building multi-agent systems that interact with large language models (LLMs) and other services. It provides a structured way to define, call, and manage agents, making it easier to build complex systems that rely on asynchronous interactions and streaming data.

## Motivation

The motivation behind MiniAgents is to provide a flexible and extensible framework for building agent-based systems that can leverage the power of LLMs and other AI services. It aims to simplify the process of creating and managing agents, handling asynchronous communication, and integrating with various LLM providers.

## Features

- **Agent Management**: Easily create, manage, and chain multiple agents using the `@miniagent` decorator.
- **Chat History**: Manage chat history with support for in-memory and markdown file storage.
- **Asynchronous Interaction**: Support for asynchronous interactions between agents.
- **Streaming**: Stream data token by token or message by message.
- **LLM Integration**: Seamlessly integrate with popular LLMs like OpenAI and Anthropic.
- **Message Handling**: Robust message handling with support for nested messages and promises.
- **Immutable Messages**: Ensures that messages are immutable, making the system more predictable and easier to debug.
- **Extensibility**: Extensible architecture allows integration with various LLM providers and other services.
- **Utilities**: A set of utility functions to facilitate common tasks like dialog loops and message joining.

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

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](LICENSE).

## Things to remember (for the developers of this framework)

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders and what not should always catch BaseExceptions and not just Exceptions** when they capture errors to pass those errors as "pieces" in order for those errors to be raised at the "consumer side". This is because many of the aforementioned Promising "primitives" are often part of mechanisms that involve communications between async tasks via asyncio.Queue objects and just interrupting those promises with KeyboardInterrupt which are extended from BaseException instead of letting KeyboardInterrupt to go through the queue leads to hanging of those promises (a queue is waiting for END_OF_QUEUE sentinel forever but the task that should send it is dead).

Happy coding with MiniAgents! 🚀
