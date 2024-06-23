Here's an improved version of the README.md file for the MiniAgents framework:

# MiniAgents

MiniAgents is an asynchronous Python framework for building multi-agent systems that interact with language models (LLMs) and other services. It provides a structured way to define, call, and manage agents, making it easier to build complex systems that rely on asynchronous interactions and streaming data.

## Motivation

MiniAgents was created to simplify the development of agent-based systems that interact with large language models. It addresses several key challenges:

1. **Asynchronous Communication**: Enables non-blocking communication between agents and external services.
2. **Streaming Support**: Allows for efficient processing of data streams, both token-by-token and message-by-message.
3. **Immutability**: Ensures predictable and reproducible agent behavior through immutable messages.
4. **Flexibility**: Provides an extensible architecture that can integrate with various LLM providers and services.
5. **Composability**: Allows for easy composition and chaining of agents to create complex interaction flows.

By addressing these challenges, MiniAgents aims to provide a robust foundation for building sophisticated AI applications and research projects.

## Features

- Define agents as simple Python functions decorated with `@miniagent`
- Asynchronous and parallel execution of agents
- Streaming of messages and tokens for efficient processing
- Immutable message passing via `Frozen` pydantic models
- Integrate with OpenAI and Anthropic LLMs using `openai_agent` and `anthropic_agent`
- Flexible chat history management, including in-memory and Markdown-based persistence
- Utilities for common interaction patterns like dialog loops and agent chaining
- Promises and async iterators used extensively to enable non-blocking execution
- Built on top of the `Promising` library for managing asynchronous operations

## Installation

```bash
pip install miniagents
```

## Basic Usage

Here's a simple example of defining and using an agent:

```python
import asyncio
from miniagents import miniagent, MiniAgents, InteractionContext

@miniagent
async def simple_agent(ctx: InteractionContext) -> None:
    ctx.reply("Hello from the agent!")

async def main():
    async with MiniAgents():
        reply = await simple_agent.inquire()
        print(await reply.aresolve_messages())

asyncio.run(main())
```

## Advanced Usage

### Integrating with OpenAI

```python
from dotenv import load_dotenv
from miniagents.ext.llm.openai import openai_agent
from miniagents.miniagents import MiniAgents

load_dotenv()

llm_agent = openai_agent.fork(model="gpt-4")

async def main():
    async with MiniAgents():
        reply_sequence = llm_agent.inquire("How are you today?", max_tokens=1000, temperature=0.0)
        async for msg_promise in reply_sequence:
            async for token in msg_promise:
                print(token, end="", flush=True)
            print()

asyncio.run(main())
```

### Multiple Agents Interaction

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

async def main():
    await achain_loop([user_agent, AWAIT, assistant_agent])

if __name__ == "__main__":
    MiniAgents().run(main())
```

The `AWAIT` sentinel is used to ensure that the previous agent's response is fully processed before the next agent starts. This is crucial for maintaining the correct order of interactions in the agent chain.

## Core Concepts

- **MiniAgents**: The main context manager for running agents
- **MiniAgent**: A wrapper for an agent function that allows calling the agent
- **InteractionContext**: Provides context for the interaction, including the messages and the agent
- **Message**: Represents a message that can be sent between agents
- **MessagePromise**: A promise of a message that can be streamed token by token
- **MessageSequencePromise**: A promise of a sequence of messages that can be streamed message by message

## Utility Functions

- `adialog_loop`: Run a dialog loop between a user agent and assistant agent
- `achain_loop`: Run a loop that chains multiple agents together
- `join_messages`: Join multiple messages into a single message
- `split_messages`: Split a message into multiple messages based on a delimiter

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](LICENSE).

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

For more detailed documentation on each module and class, please refer to the docstrings in the source code. Happy coding with MiniAgents! 🚀
