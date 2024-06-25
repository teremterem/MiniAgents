Thank you for providing the source files of the MiniAgents framework. I'll improve the README.md as requested, taking into account the current state of the framework based on the provided source code. Here's the improved version of the README.md:

# MiniAgents

MiniAgents is an asynchronous Python framework for building LLM-based multi-agent systems, with a focus on immutable messages and token streaming. It provides a simple and intuitive way to define agents and their interactions, making it easier to build complex systems that rely on asynchronous communication and streaming data.

## Motivation

MiniAgents was created to address several challenges in building agent-based systems:

1. **Asynchronous Communication**: Enable non-blocking interactions between agents and language models (LLMs).
2. **Immutability**: Ensure predictable and reproducible agent behavior through immutable messages.
3. **Streaming**: Support efficient processing of large language model outputs via token streaming.
4. **Flexibility**: Provide a framework that can be easily extended to work with various LLM providers and agent types.

## Features

- **Agent Management**: Easily create, manage, and chain multiple agents using simple decorators.
- **Asynchronous Interaction**: Support for asynchronous interactions between agents.
- **Streaming**: Process data token-by-token or message-by-message for efficient handling of large outputs.
- **Immutable Messages**: Ensure that messages passed between agents are immutable, making the system more predictable and easier to debug.
- **LLM Integration**: Seamlessly integrate with popular LLMs like OpenAI and Anthropic.
- **Chat History**: Manage chat history with support for in-memory and markdown file storage.
- **Extensibility**: Easily extend the framework to work with different LLM providers or custom agent types.
- **Promises and Async Iterators**: Utilize promises and async iterators for non-blocking communication.
- **Utility Functions**: Helpful utilities for common tasks like dialog loops and message joining.

## Installation

```bash
pip install miniagents
```

## Basic Usage

Here's a simple example of how to define and use an agent:

```python
import asyncio
from miniagents import miniagent, MiniAgents, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext):
    async for message in ctx.message_promises:
        ctx.reply(f"You said: {message}")

async def main():
    async with MiniAgents():
        reply = await my_agent.inquire("Hello!")
        print(await reply)  # prints "You said: Hello!"

asyncio.run(main())
```

## Advanced Usage

### Integrating with OpenAI

Here's an example of using MiniAgents with OpenAI's GPT models:

```python
from dotenv import load_dotenv
from miniagents.ext.llm.openai import openai_agent
from miniagents.miniagents import MiniAgents

load_dotenv()

llm_agent = openai_agent.fork(model="gpt-4o-2024-05-13")

async def main():
    async with MiniAgents():
        reply_sequence = llm_agent.inquire("How are you today?", max_tokens=1000, temperature=0.0)
        async for msg_promise in reply_sequence:
            async for token in msg_promise:
                print(token, end="", flush=True)
            print()

if __name__ == "__main__":
    asyncio.run(main())
```

### Creating a Dialog Loop

Here's an example of creating a dialog loop between a user and an AI assistant:

```python
from miniagents.ext.llm.openai import openai_agent
from miniagents.ext.misc_agents import console_user_agent
from miniagents.utils import adialog_loop
from miniagents.miniagents import MiniAgents

async def main():
    assistant_agent = openai_agent.fork(model="gpt-4o-2024-05-13")

    async with MiniAgents():
        await adialog_loop(console_user_agent, assistant_agent)

asyncio.run(main())
```

This will start an interactive dialog where the user can chat with the AI assistant in the console.

## Key Concepts

- **MiniAgents**: The main context manager for running agents and managing their lifecycle.
- **MiniAgent**: A wrapper for an agent function that allows calling the agent.
- **InteractionContext**: Provides context for the interaction, including the messages and the agent.
- **Message**: Represents a message that can be sent between agents, with optional metadata.
- **MessagePromise**: A promise of a message that can be streamed token by token.
- **MessageSequencePromise**: A promise of a sequence of messages that can be streamed message by message.

## Utility Functions

MiniAgents provides several utility functions to help with common tasks:

- **join_messages**: Join multiple messages into a single message.
- **split_messages**: Split a message into multiple messages based on a delimiter.
- **adialog_loop**: Run a dialog loop between a user agent and assistant agent.
- **achain_loop**: Run a loop that chains multiple agents together.

## Error Handling

Exceptions in agents are treated as messages, allowing for graceful error handling and recovery in multi-agent systems. This approach enables you to build robust systems that can handle unexpected situations without crashing.

## Extending MiniAgents

You can extend the functionality of MiniAgents by creating custom agents, message types, and chat history handlers. The framework is designed to be modular and flexible, allowing you to integrate it with various services and customize its behavior to fit your needs.

## FAQ

1. **Q: How does MiniAgents differ from other agent frameworks?**
   A: MiniAgents focuses on asynchronous execution, immutable message passing, and easy integration with LLMs. It's designed for building complex, streaming-capable multi-agent systems with a simple API.

2. **Q: Can I use MiniAgents with LLM providers other than OpenAI and Anthropic?**
   A: Yes, the framework is extensible. You can create custom agents for other LLM providers by following the patterns in the existing implementations.

3. **Q: How does token streaming work in MiniAgents?**
   A: Token streaming is implemented using the `StreamedPromise` class, which allows for piece-by-piece consumption of LLM outputs.

4. **Q: What are the benefits of using immutable messages?**
   A: Immutable messages ensure that the state of conversations remains consistent and predictable. This helps prevent bugs related to unexpected state changes and makes it easier to reason about the flow of information between agents.

5. **Q: How can I persist chat history in MiniAgents?**
   A: MiniAgents provides built-in support for in-memory chat history and Markdown-based persistence. You can also create custom chat history handlers by extending the `ChatHistory` class.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](../LICENSE).

---

For more advanced usage and detailed documentation on each module and class, please refer to the docstrings in the source code.
