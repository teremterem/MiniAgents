# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of agents that interact with each other through messages. It provides a robust and flexible architecture for building complex agent-based systems, including integrations with large language models (LLMs) like OpenAI and Anthropic.

## Features

- **Agent Management**: Define and manage agents using simple decorators.
- **Message Handling**: Send and receive messages between agents with support for streaming.
- **Chat History**: Manage chat history in memory or in markdown files.
- **LLM Integration**: Seamlessly integrate with OpenAI and Anthropic language models.
- **Promise-Based Architecture**: Use promises for asynchronous message handling and streaming.

## Installation

To install MiniAgents, you can use pip:

```bash
pip install miniagents
```

## Quick Start

### Defining Agents

You can define an agent using the `@miniagent` decorator. Here's a simple example:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def echo_agent(ctx: InteractionContext) -> None:
    for message in ctx.messages:
        ctx.reply(message)
```

### Running Agents

To run agents, you need to create a `MiniAgents` context:

```python
from miniagents.miniagents import MiniAgents

async def main():
    async with MiniAgents():
        response = await echo_agent.inquire("Hello, MiniAgents!")
        print(response)

import asyncio
asyncio.run(main())
```

### Integrating with LLMs

MiniAgents provides built-in support for integrating with OpenAI and Anthropic language models.

#### OpenAI Integration

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent(model="gpt-3.5-turbo")

async def main():
    async with MiniAgents():
        response = await openai_agent.inquire("Tell me a joke.")
        print(response)

import asyncio
asyncio.run(main())
```

#### Anthropic Integration

```python
from miniagents.ext.llm.anthropic import create_anthropic_agent

anthropic_agent = create_anthropic_agent(model="claude-3")

async def main():
    async with MiniAgents():
        response = await anthropic_agent.inquire("What's the weather like today?")
        print(response)

import asyncio
asyncio.run(main())
```

### Managing Chat History

You can manage chat history in memory or in markdown files.

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

### Console User Agent

You can create a user agent that interacts through the console:

```python
from miniagents.ext.console_user_agent import create_console_user_agent

user_agent = create_console_user_agent()

async def main():
    async with MiniAgents():
        await user_agent.inquire("Hello, user!")

import asyncio
asyncio.run(main())
```

## Testing

MiniAgents comes with a comprehensive test suite. To run the tests, you can use pytest:

```bash
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on GitHub.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the developers and contributors of the libraries and tools that made this project possible.

---

Happy coding with MiniAgents! If you have any questions or need further assistance, feel free to reach out.
