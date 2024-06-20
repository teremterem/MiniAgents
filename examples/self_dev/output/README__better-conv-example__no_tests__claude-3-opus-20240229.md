# MiniAgents

MiniAgents is an asynchronous framework for building LLM-based multi-agent systems in Python, with a focus on immutable messages and token streaming.

## Features

- Asynchronous architecture for efficient and scalable agent interactions
- Immutable messages for predictable and reproducible agent behavior
- Token streaming for real-time processing of LLM-generated content
- Integration with popular LLM providers like OpenAI and Anthropic
- Flexible and extensible design for building custom agents and behaviors
- Utilities for common tasks like conversation loops and message splitting/joining

## Installation

You can install MiniAgents using pip:

```bash
pip install miniagents
```

## Usage

Here's a simple example of how to use MiniAgents to create a conversation loop between a user agent and an OpenAI-powered assistant agent:

```python
from miniagents.ext.console_user_agent import create_console_user_agent
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.miniagents import MiniAgents
from miniagents.utils import adialog_loop

async def amain() -> None:
    chat_history = InMemoryChatHistory()
    try:
        print()
        await adialog_loop(
            user_agent=create_console_user_agent(chat_history=chat_history),
            assistant_agent=create_openai_agent(model="gpt-4"),
        )
    except KeyboardInterrupt:
        print()

if __name__ == "__main__":
    MiniAgents().run(amain())
```

This will start an interactive conversation where the user can chat with the OpenAI assistant. The conversation history is stored in memory.

## Documentation

The framework consists of several key components:

- `MiniAgents`: The main context manager class for configuring and running agent systems
- `MiniAgent`: A wrapper class for agent functions that allows calling the agent
- `Message`: An immutable class representing messages passed between agents
- `MessagePromise`: A promise of a message that can be streamed token by token
- `MessageSequence`: A sequence of messages that can be asynchronously flattened and resolved
- `ChatHistory`: An abstract class for loading and storing chat history

The `ext` package contains integrations with external services:

- `console_user_agent`: A user agent that interacts via the console
- `llm`: Integrations with LLM providers like OpenAI and Anthropic

The `utils` module provides utility functions for common tasks:

- `adialog_loop`: Run a dialog loop between a user agent and assistant agent
- `achain_loop`: Run a loop that chains multiple agents together
- `join_messages`: Join multiple messages into a single message
- `split_messages`: Split a message into multiple messages based on delimiters

Refer to the docstrings and type annotations in the source code for more detailed documentation on the various classes and functions.

## Contributing

Contributions are welcome! Please see the contributing guidelines for more information.

## License

MiniAgents is released under the MIT License. See LICENSE for details.
