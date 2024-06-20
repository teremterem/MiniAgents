Here's a README.md for your MiniAgents framework:

# MiniAgents

MiniAgents is an asynchronous framework for building LLM-based multi-agent systems in Python, with a focus on immutable messages and token streaming.

## Features

- Asynchronous architecture for building multi-agent systems
- Immutable messages for reliable communication between agents
- Token streaming for efficient processing of large language model outputs
- Integration with OpenAI and Anthropic language models
- Flexible message handling and persistence
- Promising-based programming model for managing asynchronous operations

## Installation

You can install MiniAgents using pip:

```
pip install miniagents
```

## Usage

Here's a simple example of using MiniAgents to create a conversation between a user and an AI assistant:

```python
from miniagents.ext.chat_history_md import ChatHistoryMD
from miniagents.ext.console_user_agent import create_console_user_agent
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.miniagents import MiniAgents
from miniagents.utils import adialog_loop

async def amain() -> None:
    chat_history = ChatHistoryMD("CHAT.md")
    try:
        await adialog_loop(
            user_agent=create_console_user_agent(chat_history=chat_history),
            assistant_agent=create_openai_agent(model="gpt-4o-2024-05-13"),
        )
    except KeyboardInterrupt:
        print()

if __name__ == "__main__":
    MiniAgents().run(amain())
```

This example creates a user agent that reads input from the console and an OpenAI agent that generates responses. The conversation is logged to a Markdown file using `ChatHistoryMD`.

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

## Examples

The `examples` directory contains several examples demonstrating how to use MiniAgents for various tasks:

- `conversation.py`: A simple conversation example using the MiniAgents framework
- `llm_example.py`: Code example for using LLM agents
- `self_dev`: Examples of using MiniAgents for self-development and documentation generation

## Tests

The `tests` directory contains unit tests for the framework. You can run the tests using pytest:

```
pytest tests
```

## Contributing

Contributions to MiniAgents are welcome! If you find a bug or have a feature request, please open an issue on the GitHub repository. If you'd like to contribute code, please fork the repository and submit a pull request.

## License

MiniAgents is released under the MIT License. See the `LICENSE` file for more information.
