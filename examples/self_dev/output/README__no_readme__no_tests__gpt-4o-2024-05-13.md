# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of agents that interact with large language models (LLMs) and other asynchronous tasks. The framework provides a structured way to define, run, and manage these agents, making it easier to build complex, multi-agent systems.

## Features

- **Agent Definition**: Easily define agents using decorators.
- **Message Handling**: Stream messages between agents with support for token-level streaming.
- **LLM Integration**: Built-in support for OpenAI and Anthropic language models.
- **Asynchronous Execution**: Fully asynchronous framework for efficient task management.
- **Extensibility**: Easily extend the framework to support new types of agents and integrations.

## Installation

To install MiniAgents, you can use [Poetry](https://python-poetry.org/):

```sh
poetry add miniagents
```

## Quick Start

Here's a quick example to get you started with MiniAgents:

### Example: Conversation with OpenAI

```python
"""
Code example for using LLMs.
"""

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
    """
    User agent that sends a message to the assistant and keeps track of the chat history.
    """
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
    """
    The main conversation loop.
    """
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

### Defining Agents

Agents are defined using the `@miniagent` decorator. An agent function takes an `InteractionContext` as its first argument and can use it to send and receive messages.

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext) -> None:
    # Your agent logic here
    ctx.reply("Hello, world!")
```

### Running Agents

To run agents, you can use the `MiniAgents` class. This class manages the lifecycle of agents and provides utilities for running them asynchronously.

```python
from miniagents.miniagents import MiniAgents

async def amain() -> None:
    # Your main logic here
    pass

if __name__ == "__main__":
    MiniAgents().run(amain())
```

### Integrating with LLMs

MiniAgents provides built-in support for integrating with OpenAI and Anthropic language models. You can create agents that interact with these models using the provided utilities.

#### OpenAI Example

```python
from miniagents.ext.llm.openai import create_openai_agent

llm_agent = create_openai_agent(model="gpt-4o-2024-05-13")
```

#### Anthropic Example

```python
from miniagents.ext.llm.anthropic import create_anthropic_agent

llm_agent = create_anthropic_agent(model="claude-3-opus-20240229")
```

### Utilities

MiniAgents provides various utility functions to help with common tasks, such as chaining agents and joining messages.

#### Chaining Agents

The `achain_loop` function allows you to chain multiple agents together in a loop.

```python
from miniagents.utils import achain_loop

await achain_loop([agent1, agent2, AWAIT])
```

#### Joining Messages

The `join_messages` function allows you to join multiple messages into a single message.

```python
from miniagents.utils import join_messages

joined_message = join_messages([message1, message2])
```

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the developers and contributors of the libraries and tools that made this project possible.

## Contact

For any questions or inquiries, please contact Oleksandr Tereshchenko at [toporok@gmail.com](mailto:toporok@gmail.com).
