# MiniAgents

MiniAgents is a Python framework for building agent-based systems, particularly those that interact with language models (LLMs) and other services. It provides a structured way to define, call, and manage agents, making it easier to build complex systems that rely on asynchronous interactions and streaming data.

## Why MiniAgents?

The motivation behind MiniAgents is to simplify the creation and management of multi-agent systems that interact with LLMs. It addresses the need for a framework that supports asynchronous interactions, streaming data, and immutable messages, making the system more predictable and easier to debug.

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

Provides context for the interaction, including the messages and the agent.

#### Message

Represents a message that can be sent between agents.

#### MessagePromise

A promise of a message that can be streamed token by token.

#### MessageSequencePromise

A promise of a sequence of messages that can be streamed message by message.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](LICENSE).

## Developer Notes

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders, and other components should always catch BaseExceptions and not just Exceptions**. This is because many of these components involve communications between async tasks via asyncio.Queue objects. Interrupting those promises with KeyboardInterrupt (which extends from BaseException) instead of letting it go through the queue can lead to hanging promises.

---

This README provides an overview of the MiniAgents framework, its features, installation instructions, usage examples, and information on testing and contributing. For more detailed documentation, please refer to the source code and comments within the project.

---

Happy coding with MiniAgents! 🚀
