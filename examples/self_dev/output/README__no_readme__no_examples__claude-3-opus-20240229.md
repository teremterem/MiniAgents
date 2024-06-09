# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides a set of tools and abstractions for defining agents, managing their interactions, and handling asynchronous communication between them.

## Features

- Define agents as simple Python functions using the `@miniagent` decorator
- Agents can send and receive messages asynchronously
- Support for streaming messages token by token
- Integration with OpenAI and Anthropic language models
- Promises and async iterators for handling asynchronous operations
- Utilities for joining and splitting message sequences
- Immutable data structures for message metadata

## Installation

You can install MiniAgents using pip:

```
pip install miniagents
```

## Usage

Here's a simple example of how to define and use agents with MiniAgents:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def hello_agent(ctx: InteractionContext):
    ctx.reply("Hello, world!")

@miniagent
async def echo_agent(ctx: InteractionContext):
    async for msg in ctx.messages:
        ctx.reply(f"You said: {msg}")

# Run the agents
async with MiniAgents():
    reply = await hello_agent.inquire()
    print(reply)  # Output: Hello, world!

    reply = await echo_agent.inquire("Hello, echo!")
    print(reply)  # Output: You said: Hello, echo!
```

## Modules

- `miniagents.miniagents`: Core classes for defining and running agents
- `miniagents.messages`: Classes for representing messages and message sequences
- `miniagents.ext.llm`: Integration with language models (OpenAI, Anthropic)
- `miniagents.promising`: Utilities for working with promises and async iterators
- `miniagents.utils`: Utility functions for working with messages

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue on the GitHub repository. If you'd like to contribute code, please fork the repository and submit a pull request.

## License

MiniAgents is released under the MIT License. See the `LICENSE` file for more information.
