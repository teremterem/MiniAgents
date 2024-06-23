Here's a clean and informative README.md for the MiniAgents framework:

# MiniAgents

MiniAgents is an asynchronous Python framework for building multi-agent systems that interact with large language models (LLMs). It focuses on immutable messages, token streaming, and efficient agent communication.

## Features

- **Asynchronous Execution**: Agents run asynchronously and can communicate in parallel.
- **Immutable Messages**: Ensures predictable and reproducible agent behavior.
- **Token Streaming**: Stream tokens from LLMs piece-by-piece for efficient processing.
- **LLM Integration**: Built-in support for OpenAI and Anthropic models.
- **Flexible Agent Definition**: Define agents as simple Python functions using the `@miniagent` decorator.
- **Promise-based Programming**: Utilizes promises and async iterators for non-blocking communication.
- **Chat History Management**: Supports in-memory and Markdown-based persistence of conversations.
- **Extensible Architecture**: Easily integrate with various LLM providers and services.

## Installation

```bash
pip install miniagents
```

## Quick Start

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

## Key Concepts

- **MiniAgents**: The main context manager for running agents.
- **MiniAgent**: A wrapper for agent functions that allows calling and chaining agents.
- **InteractionContext**: Provides context for agent interactions, including messages and reply methods.
- **Message**: Represents immutable messages passed between agents.
- **MessagePromise**: A promise of a message that can be streamed token by token.
- **MessageSequencePromise**: A promise of a sequence of messages that can be streamed message by message.

## Advanced Usage

### LLM Integration

```python
from miniagents.ext.llm.openai import openai_agent

openai_agent = openai_agent.fork(model="gpt-3.5-turbo")

async def main():
    async with MiniAgents():
        replies = openai_agent.inquire(
            "Hello, how are you?",
            system="You are a helpful assistant.",
            max_tokens=50,
            temperature=0.7,
        )
        async for reply in replies:
            print(await reply)

asyncio.run(main())
```

### Chaining Agents

```python
from miniagents.utils import achain_loop
from miniagents.promising.sentinels import AWAIT

async def main():
    await achain_loop([user_agent, AWAIT, assistant_agent])

MiniAgents().run(main())
```

## Documentation

For detailed documentation on each module and class, please refer to the docstrings in the source code.

## Contributing

Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for details.

## License

MiniAgents is released under the [MIT License](LICENSE).

---

This README provides an overview of the MiniAgents framework, its key features, installation instructions, and basic usage examples. It also touches on some advanced concepts and provides links to further documentation. You may want to expand on certain sections or add more detailed examples depending on your specific needs and target audience.
