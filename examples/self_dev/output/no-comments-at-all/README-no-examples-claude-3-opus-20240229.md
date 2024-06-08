# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides a simple and flexible way to define agents and their interactions.

## Features

- Define agents using the `@miniagent` decorator
- Agents can run in parallel and communicate with each other
- Agents can be composed to create more complex agents
- Supports streaming of messages and promises
- Integrates with OpenAI and Anthropic APIs for language model agents
- Extensible design allows adding custom agent types and behaviors

## Installation

```bash
pip install miniagents
```

## Usage

Here's a simple example of defining an agent:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def hello_agent(ctx: InteractionContext) -> None:
    ctx.reply("Hello, world!")
```

To run the agent:

```python
from miniagents.miniagents import MiniAgents

async with MiniAgents():
    reply = await hello_agent.inquire()
    print(await reply.aresolve_messages())
```

For more advanced usage, including composing agents, streaming messages, and integrating with language models, see the examples in the `examples/` directory.

## API Reference

The key classes and functions in MiniAgents are:

- `MiniAgents`: The main context manager for running agents
- `@miniagent`: Decorator for defining agents
- `InteractionContext`: Passed to agent functions, provides methods for replying and finishing early
- `Message`: Represents a message passed between agents
- `MessagePromise`: A promise that resolves to a message
- `MessageSequence`: A sequence of messages that can be streamed
- `create_openai_agent`: Creates an OpenAI language model agent
- `create_anthropic_agent`: Creates an Anthropic language model agent

For detailed API documentation, see the docstrings in the source code.

## Contributing

Contributions are welcome! Please see `CONTRIBUTING.md` for guidelines.

## License

MiniAgents is released under the MIT License. See `LICENSE` for details.
