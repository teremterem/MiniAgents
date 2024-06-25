# MiniAgents

MiniAgents is an asynchronous framework for building multi-agent systems in Python, with a focus on efficient processing of large language models (LLMs) and immutable message passing.

## Motivation

The primary motivation behind the development of MiniAgents is to provide a structured and scalable way to build complex systems that rely on interactions between various agents, including those that integrate with LLMs. The framework aims to address the following key challenges:

1. **Asynchronous Communication**: Enabling non-blocking interactions between agents and LLMs.
2. **Streaming**: Allowing agents to process data in a streaming fashion, consuming tokens or messages as they become available, rather than waiting for the entire response.
3. **Immutable Messages**: Ensuring that messages passed between agents are immutable, making the system more predictable and easier to debug.

By addressing these challenges, MiniAgents aims to simplify the development of agent-based systems that leverage the power of LLMs, while maintaining a high degree of flexibility and scalability.

## Features

- **Agent Management**: Define and manage agents using simple decorators.
- **Asynchronous Interaction**: Support for asynchronous interactions with agents.
- **Streaming**: Stream data token by token or message by message.
- **Immutable Messages**: Ensures that messages are immutable, making the system more predictable and easier to debug.
- **LLM Integration**: Seamlessly integrate with popular LLMs like OpenAI and Anthropic.
- **Message Handling**: Robust message handling with support for nested messages and promises.
- **Utilities**: A set of utility functions to facilitate common tasks like dialog loops and message joining.

## Usage

Here's a simple example of how to define an agent and initiate an interaction with it:

```python
from miniagents import miniagent, InteractionContext, MiniAgents

@miniagent
async def my_agent(ctx: InteractionContext):
    async for message in ctx.message_promises:
        ctx.reply(f"You said: {message}")

async with MiniAgents():
    reply = await my_agent.inquire("Hello!")
    print(reply)  # prints "You said: Hello!"
```

For more advanced usage, including integration with LLMs, see the [examples](examples/) directory.

## Documentation

The MiniAgents framework is organized into several modules:

- `miniagents.miniagents`: Core classes for creating and managing agents
- `miniagents.messages`: Classes for representing and handling messages
- `miniagents.promising`: Utilities for managing asynchronous operations using promises
- `miniagents.ext`: Extensions for integrating with external services and utilities

For detailed documentation on each module and class, please refer to the docstrings in the source code.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](../LICENSE).
