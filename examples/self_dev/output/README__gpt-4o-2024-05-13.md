# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides a simple and intuitive way to define agents and their interactions, with a focus on asynchronous execution, immutable message passing, and token streaming.

## Why MiniAgents?

MiniAgents was created to address the need for a robust framework that simplifies the creation and management of agents interacting with language models (LLMs) and other services. It aims to make it easier to build complex systems that rely on asynchronous interactions and streaming data.

## Features

- **Agent Management**: Easily create, manage, and chain multiple agents using simple decorators.
- **Asynchronous Communication**: Enables non-blocking interactions between agents and LLMs.
- **Streaming Support**: Allows for efficient processing of data streams, both token-by-token and message-by-message.
- **Immutable Messages**: Ensures predictable and reproducible agent behavior through immutable messages.
- **LLM Integration**: Seamlessly integrate with popular LLMs like OpenAI and Anthropic.
- **Message Handling**: Robust message handling with support for nested messages and promises.
- **Utilities**: A set of utility functions to facilitate common tasks like dialog loops and message joining.

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
    async for msg_promise in ctx.message_promises:
        async for token in msg_promise:
            print(token, end="", flush=True)
        print()
    ctx.reply(input("USER: "))

@miniagent
async def assistant_agent(ctx: InteractionContext) -> None:
    async for msg_promise in ctx.message_promises:
        async for token in msg_promise:
            print(token, end="", flush=True)
        print()
    ctx.reply("Hello, how can I assist you?")

async def amain() -> None:
    await achain_loop([user_agent, AWAIT, assistant_agent])

if __name__ == "__main__":
    MiniAgents().run(amain())
```

The `AWAIT` sentinel is used to ensure that the previous agent's response is fully processed before the next agent starts.

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
    print(await split_message)

import asyncio

asyncio.run(main())
```

## Documentation

### Modules

- `miniagents`: Core classes and functions.
- `miniagents.ext`: Extensions for integrating with external services and libraries.
- `miniagents.promising`: Classes and functions for handling promises and asynchronous operations.
- `miniagents.utils`: Utility functions for common tasks.

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

MiniAgents is released under the [MIT License](../LICENSE).

## FAQ

1. **Q: How does MiniAgents differ from other agent frameworks?**
   A: MiniAgents focuses on asynchronous execution, immutable message passing, and easy integration with LLMs. It's designed for building complex, streaming-capable multi-agent systems.

2. **Q: Can I use MiniAgents with LLM providers other than OpenAI and Anthropic?**
   A: Yes, the framework is extensible. You can create custom agents for other LLM providers by following the patterns in the existing implementations.

3. **Q: How does MiniAgents handle errors in agents?**
   A: Exceptions in agents are treated as messages, allowing for graceful error handling and recovery in multi-agent systems.

4. **Q: Is MiniAgents suitable for production use?**
   A: While MiniAgents is being actively developed, it's designed with production use cases in mind. However, always thoroughly test and evaluate it for your specific needs.

5. **Q: How can I persist agent interactions?**
   A: MiniAgents provides built-in support for chat history management, including in-memory and Markdown-based persistence options.

## Things to Remember (for Developers)

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders, and other components should always catch BaseExceptions and not just Exceptions**. This is because many of these components involve communications between async tasks via asyncio.Queue objects. Interrupting these promises with KeyboardInterrupt (which extends from BaseException) instead of letting it go through the queue can lead to hanging promises (a queue waiting for END_OF_QUEUE sentinel forever while the task that should send it is dead).

---

This README provides an overview of the MiniAgents framework, its features, installation instructions, usage examples, and information on testing and contributing. For more detailed documentation, please refer to the source code and comments within the project.

---

Happy coding with MiniAgents! 🚀
