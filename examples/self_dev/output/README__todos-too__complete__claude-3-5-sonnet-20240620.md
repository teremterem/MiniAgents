

MiniAgents is an asynchronous Python framework for building multi-agent systems that interact with large language models (LLMs). It provides a structured way to define, manage, and chain agents, with a focus on immutable messages and token streaming.

## Motivation

MiniAgents aims to simplify the creation of complex agent-based systems that rely on asynchronous interactions and streaming data from LLMs. It addresses the challenges of managing multiple agents, handling asynchronous communication, and processing streamed responses from language models in a clean and efficient manner.

## Key Features

- **Agent Management**: Easily create and chain multiple agents using simple decorators.
- **Asynchronous Communication**: Full support for asynchronous interactions between agents.
- **LLM Integration**: Seamless integration with popular LLMs like OpenAI and Anthropic.
- **Token Streaming**: Stream data token-by-token or message-by-message from LLMs.
- **Immutable Messages**: Ensure predictable and reproducible agent behavior with immutable message passing.
- **Flexible Chat History**: Manage chat history with in-memory and Markdown-based persistence options.
- **Parallel Execution**: Run agents in parallel and enable non-blocking communication.
- **Extensible Architecture**: Easily integrate with various LLM providers and extend functionality.

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
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext
from miniagents.promising.sentinels import AWAIT
from miniagents.utils import achain_loop

@miniagent
async def user_agent(ctx: InteractionContext):
    async for msg_promise in ctx.messages:
        async for token in msg_promise:
            print(token, end="", flush=True)
        print()
    ctx.reply(input("USER: "))

@miniagent
async def assistant_agent(ctx: InteractionContext):
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

The `AWAIT` sentinel is used to ensure that the previous agent's response is fully processed before the next agent starts. This prevents the agents from running in parallel and maintains the correct order of interactions in the conversation loop.

## Core Concepts

- **MiniAgents**: The main context manager for running agents and managing their lifecycle.
- **MiniAgent**: A wrapper for agent functions that allows calling and chaining agents.
- **InteractionContext**: Provides context for agent interactions, including messages and reply methods.
- **Message**: Represents immutable messages that can be sent between agents.
- **MessagePromise**: A promise of a message that can be streamed token by token.
- **MessageSequencePromise**: A promise of a sequence of messages that can be streamed message by message.

## Utilities

MiniAgents provides several utility functions to help with common tasks:

- `join_messages`: Join multiple messages into a single message.
- `split_messages`: Split a message into multiple messages based on a delimiter.
- `adialog_loop`: Run a dialog loop between a user agent and an assistant agent.
- `achain_loop`: Run a loop that chains multiple agents together.

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

For more detailed documentation on each module and class, please refer to the docstrings in the source code. The framework is designed to be modular and flexible, allowing you to integrate it with various services and customize its behavior to fit your needs.
