# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides a simple and intuitive way to define agents and their interactions, with a focus on asynchronous operations and token streaming.

## Why MiniAgents?

MiniAgents was created to simplify the development of complex systems that rely on asynchronous interactions and streaming data, particularly in the context of language models (LLMs) and other services. It provides a structured way to define, call, and manage agents, making it easier to build robust and scalable systems.

## Features

- **Agent Management**: Easily create, manage, and chain multiple agents using simple decorators.
- **Chat History**: Manage chat history with support for in-memory and markdown file storage.
- **Asynchronous Interaction**: Support for asynchronous interactions with agents.
- **Streaming**: Stream data token by token or message by message.
- **LLM Integration**: Seamlessly integrate with popular LLMs like OpenAI and Anthropic.
- **Message Handling**: Robust message handling with support for nested messages and promises.
- **Utilities**: A set of utility functions to facilitate common tasks like dialog loops and message joining.
- **Immutable Messages**: Ensures that messages are immutable, making the system more predictable and easier to debug.

## Installation

```bash
pip install miniagents
```

## Usage

### Basic Example

Here's a simple example of how to define and run an agent:

```python
import asyncio
from miniagents import miniagent, MiniAgents, InteractionContext

@miniagent
async def simple_agent(ctx: InteractionContext) -> None:
    print("Agent is running")
    ctx.reply("Hello from the agent!")

async def main() -> None:
    async with MiniAgents():
        await simple_agent.inquire()

if __name__ == "__main__":
    asyncio.run(main())
```

### Define an Agent

You can define an agent using the `@miniagent` decorator. An agent is essentially an asynchronous function that interacts with a context.

```python
from miniagents import miniagent, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext) -> None:
    ctx.reply("Hello, I am an agent!")
```

### Run an Agent

To run an agent, you need to create an instance of `MiniAgents` and use the `inquire` method to send messages to the agent.

```python
from miniagents import MiniAgents

async def main():
    async with MiniAgents():
        replies = my_agent.inquire()
        async for reply in replies:
            print(await reply)

import asyncio
asyncio.run(main())
```

### Integrate with LLMs

MiniAgents provides built-in support for OpenAI and Anthropic language models. You can create agents for these models using the provided functions.

#### OpenAI Integration

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

#### Anthropic Integration

```python
from miniagents.ext.llm.anthropic import anthropic_agent
from miniagents.messages import Message

anthropic_agent = anthropic_agent.fork(model="claude-3")

async def main():
    async with MiniAgents():
        replies = anthropic_agent.inquire(
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

### Advanced Example

For more advanced usage, you can define multiple agents and manage their interactions:

```python
from miniagents import miniagent, MiniAgents, InteractionContext
from miniagents.promising.sentinels import AWAIT
from miniagents.utils import achain_loop

@miniagent
async def user_agent(ctx: InteractionContext) -> None:
    async for msg_promise in ctx.messages:
        async for token in msg_promise:
            print(token, end="", flush=True)
        print()
    ctx.reply(input("USER: "))

@miniagent
async def assistant_agent(ctx: InteractionContext) -> None:
    async for msg_promise in ctx.messages:
        async for token in msg_promise:
            print(token, end="", flush=True)
        print()
    ctx.reply("Hello, how can I assist you?")

async def amain() -> None:
    await achain_loop([user_agent, AWAIT, assistant_agent])

if __name__ == "__main__":
    MiniAgents().run(amain())
```

### Message Handling

MiniAgents provides a structured way to handle messages using the `Message` class and its derivatives.

You can create custom message types by subclassing `Message`.

```python
from miniagents.messages import Message

class CustomMessage(Message):
    custom_field: str

message = CustomMessage(text="Hello", custom_field="Custom Value")
print(message.text)  # Output: Hello
print(message.custom_field)  # Output: Custom Value
```

## Utility Functions

### Joining Messages

You can join multiple messages into a single message using the `join_messages` function:

```python
from miniagents.utils import join_messages

async def main():
    messages = ["Hello", "world"]
    joined_message = join_messages(messages)
    print(await joined_message.aresolve())

import asyncio
asyncio.run(main())
```

### Splitting Messages

You can split a message into multiple messages using the `split_messages` function:

```python
from miniagents.utils import split_messages

async def main():
    message = "Hello\n\nworld"
    split_message = split_messages(message)
    print(await split_message.aresolve_messages())

import asyncio
asyncio.run(main())
```

## Documentation

### Modules

- `miniagents`: Core classes and functions.
- `miniagents.ext`: Extensions for integrating with external services and libraries.
- `miniagents.promising`: Classes and functions for handling promises and asynchronous operations.
- `miniagents.utils`: Utility functions for common tasks.

The framework is organized into several modules:

- `miniagents.miniagents`: Core classes for creating and managing agents.
- `miniagents.messages`: Classes for representing and handling messages.
- `miniagents.promising`: Utilities for managing asynchronous operations using promises.
- `miniagents.ext`: Extensions for integrating with external services and utilities.
  - `miniagents.ext.chat_history_md`: Chat history management using Markdown files.
  - `miniagents.ext.console_user_agent`: User agent for interacting via the console.
  - `miniagents.ext.llm`: Integration with language models.
    - `miniagents.ext.llm.openai`: OpenAI language model integration.
    - `miniagents.ext.llm.anthropic`: Anthropic language model integration.

For detailed documentation on each module and class, please refer to the docstrings in the source code.

### Extending MiniAgents

You can extend the functionality of MiniAgents by creating custom agents, message types, and chat history handlers. The framework is designed to be modular and flexible, allowing you to integrate it with various services and customize its behavior to fit your needs.

### Core Concepts

#### MiniAgents

`MiniAgents` is the main context manager that handles the lifecycle of agents and promises.

```python
from miniagents import MiniAgents

async with MiniAgents():
    # Your code here
```

#### MiniAgent

A `MiniAgent` is a wrapper for an agent function that allows calling the agent.

```python
from miniagents import miniagent

@miniagent
async def my_agent(ctx, **kwargs):
    # Agent logic here
```

#### InteractionContext

`InteractionContext` provides context for the interaction, including the messages and the agent.

```python
from miniagents import InteractionContext
```

#### Message

`Message` represents a message that can be sent between agents.

```python
from miniagents.messages import Message
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](LICENSE).

## Developer Notes

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders, and other components should always catch BaseExceptions and not just Exceptions**. This is because many of these components involve communications between async tasks via asyncio.Queue objects. Interrupting these promises with KeyboardInterrupt (which extends from BaseException) instead of letting it go through the queue can lead to hanging promises (a queue waiting for END_OF_QUEUE sentinel forever while the task that should send it is dead).

---

This README provides an overview of the MiniAgents framework, its features, installation instructions, usage examples, and information on testing and contributing. For more detailed documentation, please refer to the source code and comments within the project.

---

Happy coding with MiniAgents! 🚀
