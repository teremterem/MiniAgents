# MiniAgents

MiniAgents is an asynchronous Python framework for building multi-agent systems that interact with large language models (LLMs) and other services. It provides a structured way to define, call, and manage agents, making it easier to build complex systems that rely on asynchronous interactions and streaming data.

## Features

- **Agent Management**: Easily create, manage, and chain multiple agents using simple decorators.
- **Asynchronous Interaction**: Support for asynchronous interactions between agents and LLMs.
- **Streaming**: Efficient processing of large language model outputs via token streaming.
- **Immutable Messages**: Ensures predictable and reproducible agent behavior through immutable messages.
- **Chat History**: Manage chat history with support for in-memory and markdown file storage.
- **LLM Integration**: Seamlessly integrate with popular LLMs like OpenAI and Anthropic.
- **Extensibility**: Modular architecture allows integration with various LLM providers and customization of agent behavior.

## Installation

```bash
pip install miniagents
```

## Basic Usage

Here's a simple example of using MiniAgents to create a dialog between a user and an AI assistant powered by OpenAI's GPT-3.5-turbo model:

```python
from miniagents.ext.llm.openai import openai_agent
from miniagents.ext.misc_agents import console_user_agent
from miniagents.utils import adialog_loop


async def main():
    assistant_agent = openai_agent.fork(model="gpt-3.5-turbo")

    await adialog_loop(console_user_agent, assistant_agent)


asyncio.run(main())
```

This will start an interactive dialog where the user can chat with the AI assistant in the console.

## Advanced Usage

### Custom Message Types

You can create custom message types by subclassing the `Message` class:

```python
from miniagents.messages import Message


class CustomMessage(Message):
    custom_field: str


message = CustomMessage(text="Hello", custom_field="Custom Value")
print(message.text)  # Output: Hello
print(message.custom_field)  # Output: Custom Value
```

### Persisting Chat History

MiniAgents provides built-in support for persisting chat history to Markdown files:

```python
from miniagents.ext.history_agents import markdown_history_agent
from miniagents.ext.llm.openai import openai_agent
from miniagents.miniagents import MiniAgents
from miniagents.utils import adialog_loop

async def main():
    async with MiniAgents():
        await adialog_loop(
            user_agent=console_user_agent,
            assistant_agent=openai_agent.fork(model="gpt-3.5-turbo"),
            history_agent=markdown_history_agent.fork(history_md_file="chat_history.md")
        )

asyncio.run(main())
```

### Handling Errors in Agents

Exceptions in agents are treated as messages and can be caught and handled by other agents in the chain:

```python
from miniagents.miniagents import miniagent, MiniAgents, InteractionContext

@miniagent
async def error_handling_agent(ctx: InteractionContext):
    try:
        async for message in ctx.message_promises:
            if message.text == "error":
                raise ValueError("An error occurred")
            ctx.reply(f"Received: {message.text}")
    except ValueError as e:
        ctx.reply(f"Error: {str(e)}")

async def main():
    async with MiniAgents():
        reply = await error_handling_agent.inquire("error")
        print(await reply)

asyncio.run(main())
```

### Chaining Multiple Agents

You can use `achain_loop` to chain multiple agents together:

```python
from miniagents.miniagents import miniagent, MiniAgents, InteractionContext
from miniagents.utils import achain_loop

@miniagent
async def agent1(ctx: InteractionContext):
    ctx.reply("Message from Agent 1")

@miniagent
async def agent2(ctx: InteractionContext):
    ctx.reply("Message from Agent 2")

async def main():
    async with MiniAgents():
        await achain_loop([agent1, agent2])

asyncio.run(main())
```

### Custom Chat History Handler

You can create a custom chat history handler by extending the `ChatHistory` class:

```python
from miniagents.ext.history_agents import ChatHistory
from miniagents.miniagents import miniagent, MiniAgents, InteractionContext

class CustomChatHistory(ChatHistory):
    def __init__(self):
        self.history = []

    async def add_message(self, message):
        self.history.append(message)

    async def get_history(self):
        return self.history

@miniagent
async def custom_history_agent(ctx: InteractionContext):
    history = CustomChatHistory()
    async for message in ctx.message_promises:
        await history.add_message(message)
        ctx.reply(f"History: {await history.get_history()}")

async def main():
    async with MiniAgents():
        reply = await custom_history_agent.inquire("Hello")
        print(await reply)

asyncio.run(main())
```

## Documentation

The framework is organized into several modules:

- `miniagents.miniagents`: Core classes for creating and managing agents
- `miniagents.messages`: Classes for representing and handling messages
- `miniagents.promising`: Utilities for managing asynchronous operations using promises
- `miniagents.ext`: Extensions for integrating with external services and utilities
    - `miniagents.ext.history_agents`: Chat history management
    - `miniagents.ext.misc_agents`: Utility agents (e.g., console user agent)
    - `miniagents.ext.llm`: Integration with language models
        - `miniagents.ext.llm.openai`: OpenAI language model integration
        - `miniagents.ext.llm.anthropic`: Anthropic language model integration

For detailed documentation on each module and class, please refer to the docstrings in the source code.

## Core Concepts

- **MiniAgents**: The main class that manages the lifecycle of agents and their interactions.
- **MiniAgent**: A wrapper for an agent function that allows calling the agent.
- **InteractionContext**: Provides context for the interaction, including the messages and the agent.
- **Message**: Represents a message that can be sent between agents.
- **MessagePromise**: A promise of a message that can be streamed token by token.
- **MessageSequencePromise**: A promise of a sequence of messages that can be streamed message by message.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](LICENSE).

## FAQ

1. **Q: How does MiniAgents differ from other agent frameworks?**
   A: MiniAgents focuses on asynchronous communication, immutable messages, and seamless integration with LLMs. It provides a simple API for defining agents as Python functions while handling complex interactions behind the scenes.

2. **Q: Can I use MiniAgents with LLMs other than OpenAI and Anthropic?**
   A: Yes, the framework is designed to be extensible. You can create custom integrations for other LLM providers by following the patterns in the existing integrations.

3. **Q: How does token streaming work in MiniAgents?**
   A: MiniAgents uses `StreamedPromise` objects to handle token streaming. This allows for efficient processing of LLM responses as they are generated, rather than waiting for the entire response.

4. **Q: What are the benefits of using immutable messages?**
   A: Immutable messages ensure that the state of conversations remains consistent and predictable. This helps prevent bugs related to unexpected state changes and makes it easier to reason about the flow of information between agents.

5. **Q: How can I persist chat history in MiniAgents?**
   A: MiniAgents provides built-in support for in-memory chat history and Markdown-based persistence. You can also create custom chat history handlers by extending the `ChatHistory` class.

Happy coding with MiniAgents! 🚀
