# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of agent-based systems that interact with language models (LLMs) and other services. It provides a structured way to define, call, and manage agents, making it easier to build complex systems that rely on asynchronous interactions and streaming data.

## Why MiniAgents?

The motivation behind MiniAgents is to provide a simple and intuitive way to define agents and their interactions, especially in systems that require asynchronous and parallel execution. It aims to solve the problem of managing complex interactions between agents and LLMs, providing a robust framework for building scalable and efficient agent-based systems.

## Features

- **Asynchronous Interaction**: Support for asynchronous interactions with agents.
- **Streaming**: Stream data token by token or message by message.
- **Parallel Execution**: Asynchronous and parallel execution of agents.
- **Simple Agent Definition**: Define agents as simple Python functions decorated with `@miniagent`.
- **Inter-Agent Communication**: Agents can interact with each other by sending and receiving messages.
- **Extensible Architecture**: Integrate with various LLM providers (OpenAI, Anthropic, etc.).
- **Immutable Message Passing**: Immutable message passing via `Frozen` pydantic models.
- **Promise-Based Programming**: Built on top of the `Promising` library for managing asynchronous operations.
- **Typing and Validation**: Typing with Pydantic for validation and serialization of messages.

## Installation

```bash
pip install miniagents
```

## Usage

### Basic Example

Here's a simple example of how to define and run an agent:

```python
import asyncio
from miniagents import miniagent, InteractionContext, MiniAgents

@miniagent
async def my_agent(ctx: InteractionContext):
    async for message in ctx.messages:
        ctx.reply(f"You said: {message}")

async def main():
    async with MiniAgents():
        reply = await my_agent.inquire("Hello!")
        print(reply)  # prints "You said: Hello!"

if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced Example

For more advanced usage, you can define multiple agents and manage their interactions:

```python
import asyncio
from miniagents import miniagent, MiniAgents, InteractionContext

@miniagent
async def agent1(ctx: InteractionContext):
    ctx.reply("Hello from Agent 1!")

@miniagent
async def agent2(ctx: InteractionContext):
    message = await ctx.messages.aresolve_messages()
    ctx.reply(f"Agent 2 received: {message[0].text}")

async def main():
    async with MiniAgents():
        agent2_replies = agent2.inquire(agent1.inquire())
        print(await agent2_replies.aresolve_messages())

if __name__ == "__main__":
    asyncio.run(main())
```

This will output:
```
(Message(text='Agent 2 received: Hello from Agent 1!'),)
```

### Integrate with LLMs

MiniAgents provides built-in support for OpenAI and Anthropic language models. You can create agents for these models using the provided functions.

#### OpenAI Integration

```python
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.messages import Message

openai_agent = create_openai_agent(model="gpt-3.5-turbo")

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
from miniagents.ext.llm.anthropic import create_anthropic_agent

anthropic_agent = create_anthropic_agent()

async def main():
    async with MiniAgents():
        replies = anthropic_agent.inquire("Hello, Anthropic!")
        async for reply in replies:
            print(await reply)

import asyncio
asyncio.run(main())
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

## Core Concepts

- **MiniAgents**: The main context manager for running agents.
- **MiniAgent**: A wrapper for an agent function that allows calling the agent.
- **InteractionContext**: Provides context for an agent's interaction, including the messages and reply streamer.
- **Message**: Represents a message that can be sent between agents.
- **MessagePromise**: A promise of a message that can be streamed token by token.
- **MessageSequencePromise**: A promise of a sequence of messages that can be streamed message by message.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](LICENSE).

## Developer Notes

- **Error Handling**: Different Promise and StreamedPromise resolvers, piece streamers, appenders, and other components should always catch `BaseException` and not just `Exception` to ensure proper error handling and avoid hanging promises.

---

Happy coding with MiniAgents! 🚀
