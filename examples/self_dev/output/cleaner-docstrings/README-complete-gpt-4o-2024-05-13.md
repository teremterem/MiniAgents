# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of asynchronous agents that can interact with each other through messages. The framework is particularly useful for integrating with large language models (LLMs) such as OpenAI's GPT and Anthropic's Claude, but it is flexible enough to support a wide range of use cases.

## Features

- **Asynchronous Agents**: Create agents that can run asynchronously and interact with each other through messages.
- **LLM Integration**: Easily integrate with large language models like OpenAI's GPT and Anthropic's Claude.
- **Message Handling**: Robust message handling with support for nested messages and promises.
- **Extensible**: Easily extend the framework to support new types of agents and messages.
- **Utilities**: A set of utility functions to facilitate common tasks like message joining and splitting.

## Installation

To install MiniAgents, you can use `poetry`:

```bash
poetry add miniagents
```

Or you can install it directly from the source:

```bash
git clone https://github.com/teremterem/MiniAgents.git
cd MiniAgents
poetry install
```

## Quick Start

Here is a quick example to get you started with MiniAgents:

### Example: Conversation with OpenAI's GPT

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

- **MiniAgents**: The main class that manages the lifecycle of agents and their interactions.
- **MiniAgent**: A wrapper for an agent function that allows calling the agent.
- **InteractionContext**: Provides context for the interaction, including the messages and the agent.
- **Message**: Represents a message that can be sent between agents.
- **MessagePromise**: A promise of a message that can be streamed token by token.
- **MessageSequencePromise**: A promise of a sequence of messages that can be streamed message by message.

### Creating Agents

To create an agent, use the `@miniagent` decorator:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext) -> None:
    # Your agent logic here
    ctx.reply("Hello, world!")
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

To integrate with LLMs, use the provided functions in `miniagents.ext.llm`:

```python
from miniagents.ext.llm.openai import create_openai_agent

llm_agent = create_openai_agent(model="gpt-4o-2024-05-13")
```

## Testing

To run the tests, use `pytest`:

```bash
pytest
```

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the developers and contributors of the libraries and tools that made this project possible.
