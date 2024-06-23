

MiniAgents is an asynchronous Python framework for building multi-agent systems that interact with large language models (LLMs). It provides a structured way to define, manage, and chain agents, with a focus on immutable messages and token streaming.

## Features

- **Agent Management**: Easily create and manage multiple agents using simple decorators.
- **Asynchronous Execution**: Support for asynchronous and parallel execution of agents.
- **Message Handling**: Robust message handling with support for nested messages and promises.
- **LLM Integration**: Seamless integration with popular LLMs like OpenAI and Anthropic.
- **Streaming**: Stream data token by token or message by message.
- **Chat History**: Flexible chat history management, including in-memory and Markdown-based persistence.
- **Immutability**: Immutable messages and agent states for predictable and reproducible behavior.
- **Promises**: Extensive use of promises and async iterators for non-blocking communication.
- **Extensibility**: Easily extendable architecture for integrating with various LLM providers.

## Installation

```bash
pip install miniagents
```

## Basic Usage

Here's a simple example of defining and using an agent:

```python
from miniagents import miniagent, MiniAgents, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext):
    async for message in ctx.messages:
        ctx.reply(f"You said: {message}")

async def main():
    async with MiniAgents():
        reply = await my_agent.inquire("Hello!")
        print(await reply.aresolve_messages())

import asyncio
asyncio.run(main())
```

## Advanced Usage

### Chaining Agents

```python
from miniagents import miniagent, MiniAgents, InteractionContext

@miniagent
async def agent1(ctx: InteractionContext):
    ctx.reply("Hello from Agent 1!")

@miniagent
async def agent2(ctx: InteractionContext):
    messages = await ctx.messages.aresolve_messages()
    ctx.reply(f"Agent 2 received: {messages[0].text}")

async def main():
    async with MiniAgents():
        agent2_replies = agent2.inquire(agent1.inquire())
        print(await agent2_replies.aresolve_messages())

asyncio.run(main())
```

### Integrating with LLMs

```python
from miniagents.ext.llm.openai import openai_agent
from miniagents.messages import Message

async def main():
    async with MiniAgents():
        openai_agent_instance = openai_agent.fork(model="gpt-3.5-turbo")
        replies = openai_agent_instance.inquire(
            Message(text="Hello, how are you?", role="user"),
            system="You are a helpful assistant.",
            max_tokens=50,
            temperature=0.7,
        )
        async for reply in replies:
            print(await reply)

asyncio.run(main())
```

## Core Concepts

- **MiniAgents**: The main context manager for running agents.
- **MiniAgent**: A wrapper for an agent function that allows calling the agent.
- **InteractionContext**: Provides context for the interaction, including messages and reply methods.
- **Message**: Represents a message that can be sent between agents.
- **MessagePromise**: A promise of a message that can be streamed token by token.
- **MessageSequencePromise**: A promise of a sequence of messages that can be streamed message by message.

## Utility Functions

- `adialog_loop`: Run a dialog loop between a user agent and assistant agent.
- `achain_loop`: Run a loop that chains multiple agents together.
- `join_messages`: Join multiple messages into a single message.
- `split_messages`: Split messages based on a delimiter.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](LICENSE).

For more detailed documentation and examples, please refer to the source code and comments within the project.
