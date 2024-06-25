# MiniAgents

MiniAgents is an asynchronous Python framework for building multi-agent systems that interact with large language models (LLMs) and other services. It provides a structured way to define, call, and manage agents, making it easier to build complex systems that rely on asynchronous interactions and streaming data.

## Features

- **Agent Management**: Easily create, manage, and chain multiple agents using simple decorators.
- **Asynchronous Interaction**: Support for asynchronous interactions between agents and LLMs.
- **Streaming**: Efficiently process large language model outputs via token streaming.
- **Immutable Messages**: Ensure predictable and reproducible agent behavior through immutable messages.
- **Chat History**: Manage chat history with support for in-memory and markdown file storage.
- **LLM Integration**: Seamlessly integrate with popular LLMs like OpenAI and Anthropic.
- **Utilities**: A set of utility functions to facilitate common tasks like dialog loops and agent chaining.

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

In this example:

1. We take `console_user_agent`, which reads user input from the console and writes back to the console.
2. We create an assistant agent using `openai_agent.fork()`, specifying the OpenAI model to use (e.g., "gpt-3.5-turbo").
3. We start a dialog loop using `adialog_loop()`, passing the user agent and assistant agent as arguments.
4. The dialog loop runs asynchronously within the `MiniAgents` context, allowing the agents to interact and exchange messages.

## Advanced Usage

### Defining Agents

You can define an agent using the `@miniagent` decorator. An agent is essentially an asynchronous function that interacts with a context.

```python
from miniagents.miniagents import miniagent, InteractionContext


@miniagent
async def my_agent(ctx: InteractionContext) -> None:
    ctx.reply("Hello, I am an agent!")
```

### Running Agents

To run an agent, you need to create an instance of `MiniAgents` and use the `inquire` method to send messages to the agent.

```python
from miniagents.miniagents import MiniAgents


async def main():
    async with MiniAgents():
        replies = my_agent.inquire()
        async for reply in replies:
            print(await reply)


import asyncio

asyncio.run(main())
```

### Integrating with LLMs

MiniAgents provides built-in support for OpenAI and Anthropic language models. You can create agents for these models using the provided functions.

```python
from miniagents.ext.llm.openai import openai_agent
from miniagents.messages import Message

openai_agent = openai_agent.fork(model="gpt-3.5-turbo")


async def main():
    async with MiniAgents():
        replies = openai_agent.inquire(
            Message(text="Hello, how are you?", role="user"),
            system="You are a helpful assistant.",
            max_tokens=50,
            temperature=0.7,
        )
        async for reply in replies:
            print(await reply)


import asyncio

asyncio.run(main())
```

### Handling Messages

MiniAgents provides a structured way to handle messages. You can define different types of messages such as `UserMessage`, `SystemMessage`, and `AssistantMessage`:

```python
from miniagents.ext.llm.llm_common import UserMessage, SystemMessage, AssistantMessage

user_message = UserMessage(text="Hello!")
system_message = SystemMessage(text="System message")
assistant_message = AssistantMessage(text="Assistant message")
```

Exceptions in agents are treated as messages and can be caught and handled by other agents in the chain.

### Utilities

MiniAgents provides several utility functions to help with common tasks:

- **adialog_loop**: Run a dialog loop between a user agent and assistant agent.
- **achain_loop**: Run a loop that chains multiple agents together.
- **join_messages**: Join multiple messages into a single message using a delimiter.
- **split_messages**: Split a message into multiple messages based on a delimiter.

Example of joining messages:

```python
from miniagents.utils import join_messages


async def main():
    async with MiniAgents() as context:
        joined_message = join_messages(["Hello", "World"], delimiter=" ")
        print(await joined_message.aresolve())


MiniAgents().run(main())
```

## Documentation

The framework is organized into several modules:

- `miniagents.miniagents`: Core classes for creating and managing agents
- `miniagents.messages`: Classes for representing and handling messages
- `miniagents.promising`: Utilities for managing asynchronous operations using promises
- `miniagents.ext`: Extensions for integrating with external services and utilities
    - `miniagents.ext.history_agents`: Chat history management
    - `miniagents.ext.misc_agents`: Miscellaneous agents like console user agent
    - `miniagents.ext.llm`: Integration with language models
        - `miniagents.ext.llm.openai`: OpenAI language model integration
        - `miniagents.ext.llm.anthropic`: Anthropic language model integration

For detailed documentation on each module and class, please refer to the docstrings in the source code.

### Core Classes

- `MiniAgents`: The main class that manages the lifecycle of agents and their interactions.
- `MiniAgent`: A wrapper for an agent function that allows calling the agent.
- `InteractionContext`: Provides context for the interaction, including the messages and the agent.
- `Message`: Represents a message that can be sent between agents.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](../LICENSE).

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

## Things to remember (for the developers of this framework)

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders, and other components should always catch BaseExceptions and not just Exceptions**. This is because many of these components involve communications between async tasks via asyncio.Queue objects. Interrupting those promises with KeyboardInterrupt (which extends from BaseException) instead of letting it go through the queue can lead to hanging promises (a queue waiting for END_OF_QUEUE sentinel forever while the task that should send it is dead).

Happy coding with MiniAgents! 🚀
