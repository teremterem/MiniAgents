# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of asynchronous agents that can interact with each other through messages. It provides a structured way to define, run, and manage agents, making it easier to build complex systems that require asynchronous communication and coordination.

## Features

- **Asynchronous Agents**: Define agents that can run asynchronously and interact with each other through messages.
- **Message Handling**: Use a flexible message system to send and receive messages between agents.
- **LLM Integration**: Integrate with large language models (LLMs) like OpenAI and Anthropic to create intelligent agents.
- **Promise-Based Architecture**: Utilize promises to handle asynchronous operations and message streaming.
- **Extensible**: Easily extend the framework to add new functionalities and integrations.

## Installation

To install MiniAgents, you can use `poetry`:

```bash
poetry add miniagents
```

## Getting Started

Here is a simple example to get you started with MiniAgents:

### Example: Conversation with LLM

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

## Documentation

### Core Concepts

- **MiniAgent**: The core building block of the framework. Define agents using the `@miniagent` decorator.
- **InteractionContext**: Provides the context for agent interactions, including message handling.
- **Message**: Represents a message that can be sent between agents.
- **MessagePromise**: A promise of a message that can be streamed token by token.
- **MessageSequencePromise**: A promise of a sequence of messages that can be streamed message by message.

### Creating Agents

To create an agent, use the `@miniagent` decorator:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext) -> None:
    async for msg_promise in ctx.messages:
        async for token in msg_promise:
            print(token, end="", flush=True)
    ctx.reply("Response from my_agent")
```

### Running Agents

To run agents, use the `MiniAgents` context manager:

```python
from miniagents.miniagents import MiniAgents

async def amain() -> None:
    # Your main logic here

if __name__ == "__main__":
    MiniAgents().run(amain())
```

### Integrating with LLMs

MiniAgents provides integration with LLMs like OpenAI and Anthropic. Use the provided functions to create LLM agents:

```python
from miniagents.ext.llm.openai import create_openai_agent

llm_agent = create_openai_agent(model="gpt-4o-2024-05-13")
```

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the contributors and the open-source community for their support and contributions.
