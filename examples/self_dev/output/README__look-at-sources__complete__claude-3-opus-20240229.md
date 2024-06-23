Here's an improved version of the README.md file for the MiniAgents framework:

# MiniAgents

MiniAgents is an asynchronous Python framework for building multi-agent systems that interact with large language models (LLMs) and other services. It provides a structured way to define, call, and manage agents, making it easier to build complex systems that rely on asynchronous interactions and streaming data.

## Motivation

The motivation behind MiniAgents is to provide a flexible and extensible framework for building agent-based systems that can leverage the power of LLMs. It aims to simplify the process of creating and managing agents, handling asynchronous interactions, and integrating with various LLM providers.

## Features

- **Agent Management**: Easily create, manage, and chain multiple agents using the `@miniagent` decorator.
- **Chat History**: Manage chat history with support for in-memory and markdown file storage.
- **Asynchronous Interaction**: Support for asynchronous interactions between agents.
- **Streaming**: Stream data token by token or message by message.
- **LLM Integration**: Seamlessly integrate with popular LLMs like OpenAI and Anthropic.
- **Message Handling**: Robust message handling with support for nested messages and promises.
- **Immutable Messages**: Ensures that messages are immutable, making the system more predictable and easier to debug.
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

### Core Classes

- `MiniAgents`: The main context manager for running agents.
- `MiniAgent`: A wrapper for an agent function that allows calling the agent.
- `InteractionContext`: Provides context for the interaction, including the messages and the agent.
- `Message`: Represents a message that can be sent between agents.

### Message Handling

- `MessagePromise`: A promise of a message that can be streamed token by token.
- `MessageSequencePromise`: A promise of a sequence of messages that can be streamed message by message.

### Utilities

- `adialog_loop`: Run a dialog loop between a user agent and assistant agent.
- `achain_loop`: Runs a loop of agents, chaining their interactions.
- `join_messages`: Joins multiple messages into a single message using a delimiter.
- `split_messages`: Splits messages based on a delimiter.

For detailed documentation on each module and class, please refer to the docstrings in the source code.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](LICENSE).

## Things to Remember

- Different Promise and StreamedPromise resolvers, piece streamers, appenders, etc. should always catch BaseExceptions and not just Exceptions when they capture errors to pass those errors as "pieces". This ensures that errors like KeyboardInterrupt are properly handled and do not lead to hanging promises.

Happy coding with MiniAgents! 🚀
