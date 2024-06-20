# MiniAgents

MiniAgents is an asynchronous framework for building LLM-based multi-agent systems in Python, with a focus on immutable messages and token streaming.

## Features

- **Asynchronous**: Built with async/await for high performance and scalability.
- **LLM Integration**: Supports integration with popular large language models (LLMs) like OpenAI and Anthropic.
- **Immutable Messages**: Ensures message immutability for consistency and reliability.
- **Token Streaming**: Supports token streaming for efficient message handling.
- **Extensible**: Easily extendable to support custom agents and message types.

## Installation

You can install MiniAgents using [Poetry](https://python-poetry.org/):

```sh
poetry add miniagents
```

## Quick Start

Here's a quick example to get you started with MiniAgents:

```python
import asyncio
from miniagents import MiniAgents, miniagent, Message

@miniagent
async def echo_agent(ctx, **kwargs):
    async for message in ctx.messages:
        ctx.reply(message)

async def main():
    async with MiniAgents():
        agent = echo_agent()
        response = await agent.inquire(Message(text="Hello, MiniAgents!")).aresolve_messages()
        print(response)

asyncio.run(main())
```

## Documentation

### Core Concepts

#### MiniAgents

`MiniAgents` is the main context manager that handles the lifecycle of agents and promises.

```python
from miniagents import MiniAgents

async with MiniAgents():
    # Your code here
```

#### MiniAgent

A `MiniAgent` is a wrapper for an agent function that allows calling the agent.

```python
from miniagents import miniagent

@miniagent
async def my_agent(ctx, **kwargs):
    # Agent logic here
```

#### Message

`Message` is the base class for messages that can be sent between agents.

```python
from miniagents import Message

message = Message(text="Hello, World!")
```

### Utilities

#### `adialog_loop`

Runs a loop that chains the user agent and the assistant agent in a dialog.

```python
from miniagents.utils import adialog_loop

await adialog_loop(user_agent, assistant_agent)
```

#### `achain_loop`

Runs a loop that chains the agents together.

```python
from miniagents.utils import achain_loop

await achain_loop([agent1, agent2, agent3])
```

## Extending MiniAgents

### Custom Agents

You can create custom agents by defining a function and decorating it with `@miniagent`.

```python
from miniagents import miniagent, InteractionContext

@miniagent
async def custom_agent(ctx: InteractionContext, **kwargs):
    # Custom agent logic here
```

### Custom Message Types

You can create custom message types by subclassing `Message`.

```python
from miniagents import Message

class CustomMessage(Message):
    custom_field: str
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on GitHub.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the contributors and the open-source community for their support and contributions.

## Contact

For any questions or inquiries, please contact Oleksandr Tereshchenko at [toporok@gmail.com](mailto:toporok@gmail.com).

---

Happy coding with MiniAgents! 🚀
