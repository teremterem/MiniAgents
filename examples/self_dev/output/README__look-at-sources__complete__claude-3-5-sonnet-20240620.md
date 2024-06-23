Here's an improved version of the README.md file for the MiniAgents framework:

# MiniAgents

MiniAgents is an asynchronous Python framework for building multi-agent systems that interact with large language models (LLMs). It provides a structured way to define, manage, and chain agents, with a focus on immutable messages and token streaming.

## Motivation

MiniAgents was created to simplify the development of complex, asynchronous agent-based systems that interact with LLMs. It addresses several key challenges:

1. **Asynchronous Communication**: Enables non-blocking interactions between agents and LLMs.
2. **Immutability**: Ensures predictable and reproducible agent behavior through immutable messages.
3. **Streaming**: Supports efficient processing of large language model outputs via token streaming.
4. **Flexibility**: Allows easy integration with various LLM providers and extensibility for custom use cases.
5. **Composability**: Facilitates the creation of complex systems by chaining and composing simpler agents.

## Features

- Define agents as simple Python functions decorated with `@miniagent`
- Asynchronous and parallel execution of agents
- Immutable message passing using `Frozen` Pydantic models
- Integration with OpenAI and Anthropic LLMs
- Token streaming from LLMs using `StreamedPromise`
- Flexible chat history management (in-memory and Markdown-based persistence)
- Utilities for common interaction patterns (dialog loops, agent chaining)
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

## LLM Integration

MiniAgents provides built-in support for OpenAI and Anthropic language models:

```python
from miniagents.ext.llm.openai import openai_agent
from miniagents.messages import Message

async def main():
    async with MiniAgents():
        openai_gpt = openai_agent.fork(model="gpt-3.5-turbo")
        replies = openai_gpt.inquire(
            Message(text="Hello, how are you?", role="user"),
            system="You are a helpful assistant.",
            max_tokens=50,
            temperature=0.7,
        )
        async for reply in replies:
            print(await reply)

asyncio.run(main())
```

## Advanced Usage

### Chaining Agents

You can create more complex interactions by chaining multiple agents:

```python
from miniagents import miniagent, MiniAgents, InteractionContext
from miniagents.promising.sentinels import AWAIT
from miniagents.utils import achain_loop

@miniagent
async def user_agent(ctx: InteractionContext) -> None:
    user_input = input("USER: ")
    ctx.reply(user_input)

@miniagent
async def assistant_agent(ctx: InteractionContext) -> None:
    async for msg in ctx.messages:
        print(f"ASSISTANT: {msg}")
    ctx.reply("How can I assist you?")

async def main():
    async with MiniAgents():
        await achain_loop([user_agent, AWAIT, assistant_agent])

asyncio.run(main())
```

The `AWAIT` sentinel is used to ensure that the previous agent's response is fully processed before the next agent starts.

### Message Handling

MiniAgents provides a structured way to handle messages:

```python
from miniagents.messages import Message
from miniagents.ext.llm.llm_common import UserMessage, SystemMessage, AssistantMessage

user_message = UserMessage(text="Hello!")
system_message = SystemMessage(text="You are a helpful assistant.")
assistant_message = AssistantMessage(text="How can I help you today?")
```

### Utility Functions

MiniAgents offers several utility functions for common tasks:

```python
from miniagents.utils import join_messages, split_messages

async def main():
    async with MiniAgents() as context:
        joined_message = join_messages(["Hello", "World"], delimiter=" ")
        print(await joined_message.aresolve())

        split_message = split_messages("Hello\n\nWorld")
        print(await split_message.aresolve_messages())

MiniAgents().run(main())
```

## Documentation

For detailed documentation on each module and class, please refer to the docstrings in the source code. The main modules are:

- `miniagents.miniagents`: Core classes for creating and managing agents
- `miniagents.messages`: Classes for representing and handling messages
- `miniagents.promising`: Utilities for managing asynchronous operations
- `miniagents.ext`: Extensions for integrating with external services and utilities

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](LICENSE).

## FAQ

Q: How does MiniAgents handle errors in agents?
A: Exceptions in agents are treated as messages and can be caught and handled by other agents in the chain.

Q: Can I use MiniAgents with other LLM providers?
A: Yes, the framework is designed to be extensible. You can create custom agents for other LLM providers by following the patterns used for OpenAI and Anthropic integrations.

Q: How does token streaming work in MiniAgents?
A: Token streaming is implemented using the `StreamedPromise` class, which allows for piece-by-piece consumption of LLM outputs.

Q: Is MiniAgents suitable for production use?
A: While MiniAgents is actively developed and used in various projects, it's always recommended to thoroughly test and evaluate the framework for your specific use case before deploying to production.

---

Happy coding with MiniAgents! 🚀
