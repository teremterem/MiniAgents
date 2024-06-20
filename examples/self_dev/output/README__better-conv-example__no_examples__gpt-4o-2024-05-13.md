# MiniAgents

MiniAgents is an asynchronous framework for building LLM-based multi-agent systems in Python, with a focus on immutable messages and token streaming.

## Features

- **Asynchronous**: Built with asyncio for high concurrency.
- **Immutable Messages**: Ensures that messages are immutable, making the system more predictable and easier to debug.
- **Token Streaming**: Supports token-level streaming for efficient and responsive interactions.
- **Multi-Agent Systems**: Facilitates the creation of complex multi-agent systems with ease.

## Installation

You can install MiniAgents using [Poetry](https://python-poetry.org/):

```sh
poetry add miniagents
```

## Quick Start

Here's a quick example to get you started with MiniAgents:

```python
import asyncio
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext

@miniagent
async def echo_agent(ctx: InteractionContext) -> None:
    for message in ctx.messages:
        ctx.reply(message)

async def main():
    async with MiniAgents():
        response = await echo_agent.inquire("Hello, MiniAgents!").aresolve_messages()
        print(response)

asyncio.run(main())
```

## Core Concepts

### MiniAgents

The `MiniAgents` class is the core context manager that handles the lifecycle of agents and their interactions.

### MiniAgent

A `MiniAgent` is a wrapper for an agent function that allows calling the agent. You can create a MiniAgent using the `@miniagent` decorator.

### InteractionContext

The `InteractionContext` class provides the context in which an agent operates. It includes the messages received by the agent and methods to reply to those messages.

### Message

The `Message` class represents a message that can be sent between agents. Messages are immutable and can be streamed token by token.

## Advanced Usage

### Creating a Console User Agent

You can create a user agent that reads input from the console and keeps track of the chat history:

```python
from miniagents.ext.console_user_agent import create_console_user_agent

user_agent = create_console_user_agent()
```

### Integrating with LLMs

MiniAgents supports integration with various LLMs like OpenAI and Anthropic.

#### OpenAI

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent(model="gpt-3.5-turbo")
```

#### Anthropic

```python
from miniagents.ext.llm.anthropic import create_anthropic_agent

anthropic_agent = create_anthropic_agent(model="claude-3")
```

### Chat History Management

MiniAgents provides abstractions for managing chat history. You can store chat history in memory or in a markdown file.

#### In-Memory Chat History

```python
from miniagents.chat_history import InMemoryChatHistory

chat_history = InMemoryChatHistory()
```

#### Markdown Chat History

```python
from miniagents.ext.chat_history_md import ChatHistoryMD

chat_history_md = ChatHistoryMD("chat_history.md")
```

## Testing

MiniAgents comes with a comprehensive test suite. You can run the tests using `pytest`:

```sh
pytest
```

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the contributors and the open-source community for their support and contributions.

## Contact

For any questions or suggestions, feel free to open an issue on [GitHub](https://github.com/teremterem/MiniAgents) or contact the author at [toporok@gmail.com](mailto:toporok@gmail.com).
