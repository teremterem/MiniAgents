# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of agents that interact with each other asynchronously. It is particularly useful for building applications that involve complex interactions between multiple agents, such as chatbots, automated customer support systems, and other AI-driven applications.

## Features

- **Asynchronous Communication**: MiniAgents leverages Python's `asyncio` to enable asynchronous communication between agents.
- **LLM Integration**: Built-in support for integrating with large language models (LLMs) from providers like OpenAI and Anthropic.
- **Message Streaming**: Stream messages token by token, allowing for real-time interaction and response generation.
- **Promise-Based Architecture**: Utilizes a promise-based architecture to handle asynchronous operations and error management.
- **Extensible**: Easily extendable to support new types of agents and interactions.

## Installation

To install MiniAgents, you can use `poetry`:

```bash
poetry add miniagents
```

## Quick Start

Here's a simple example to get you started with MiniAgents:

### Example: Conversation with an LLM

```python
import readline  # pylint: disable=unused-import
from dotenv import load_dotenv
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.miniagent_typing import MessageType
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext
from miniagents.promising.sentinels import AWAIT
from miniagents.utils import achain_loop

load_dotenv()

CHAT_HISTORY: list[MessageType] = []

@miniagent
async def user_agent(ctx: InteractionContext) -> None:
    print("\033[92;1m", end="", flush=True)
    async for msg_promise in ctx.messages:
        print(f"\n{msg_promise.preliminary_metadata.agent_alias}: ", end="", flush=True)
        async for token in msg_promise:
            print(token, end="", flush=True)
        print("\n")

    CHAT_HISTORY.append(ctx.messages)
    print("\033[93;1m", end="", flush=True)
    CHAT_HISTORY.append(input("USER: "))

    ctx.reply(CHAT_HISTORY)

async def amain() -> None:
    try:
        print()
        await achain_loop(
            [
                user_agent,
                AWAIT,
                create_openai_agent(model="gpt-4o-2024-05-13"),
            ]
        )
    except KeyboardInterrupt:
        ...
    finally:
        print("\033[0m\n")

if __name__ == "__main__":
    MiniAgents().run(amain())
```

## Documentation

### Core Concepts

#### MiniAgents

The `MiniAgents` class is the core of the framework. It manages the lifecycle of agents and their interactions.

#### MiniAgent

A `MiniAgent` is a wrapper around an agent function. It allows the function to be called asynchronously and to interact with other agents.

#### InteractionContext

The `InteractionContext` class provides the context in which an agent operates. It includes the messages received by the agent and a method to send replies.

#### Message

The `Message` class represents a message that can be sent between agents. It supports streaming of message tokens.

### Creating Agents

To create an agent, use the `@miniagent` decorator:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext) -> None:
    async for msg_promise in ctx.messages:
        async for token in msg_promise:
            print(token, end="", flush=True)
    ctx.reply("Hello, world!")
```

### Running Agents

To run agents, use the `MiniAgents` class:

```python
from miniagents.miniagents import MiniAgents

async def amain() -> None:
    # Your async code here

if __name__ == "__main__":
    MiniAgents().run(amain())
```

### Integrating with LLMs

MiniAgents provides built-in support for integrating with LLMs from providers like OpenAI and Anthropic. Use the `create_openai_agent` or `create_anthropic_agent` functions to create agents that interact with these models.

```python
from miniagents.ext.llm.openai import create_openai_agent

llm_agent = create_openai_agent(model="gpt-4o-2024-05-13")
```

## Examples

### Example: Using LLMs

```python
from pprint import pprint
from dotenv import load_dotenv
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.messages import Message
from miniagents.miniagents import MiniAgents

load_dotenv()

llm_agent = create_openai_agent(model="gpt-4o-2024-05-13")
mini_agents = MiniAgents()

@mini_agents.on_persist_message
async def persist_message(_, message: Message) -> None:
    print("HASH KEY:", message.hash_key)
    print(type(message).__name__)
    pprint(message.serialize(), width=119)
    print()

async def amain() -> None:
    reply_sequence = llm_agent.inquire(
        "How are you today?",
        max_tokens=1000,
        temperature=0.0,
        system="Respond only in Yoda-speak.",
    )

    print()
    async for msg_promise in reply_sequence:
        async for token in msg_promise:
            print(f"\033[92;1m{token}\033[0m", end="", flush=True)
        print()
        print()

if __name__ == "__main__":
    mini_agents.run(amain())
```

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the developers and contributors of the libraries and tools that made this project possible.
