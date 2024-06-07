Here is a README.md for the MiniAgents framework:

# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides abstractions and utilities for defining agents, passing messages between agents, and managing the execution flow of agent interactions.

## Key Features

- Define agents as simple Python functions decorated with `@miniagent`
- Pass messages between agents using `MessageType` and `MessageSequencePromise`
- Manage agent execution flow with utilities like `achain_loop`
- Integrate with LLMs like OpenAI and Anthropic to create AI-powered agents
- Stream tokens from LLMs for real-time agent interactions
- Persist messages with customizable `on_persist_message` handlers
- Freeze mutable message data to ensure data integrity
- Extensive promise-based abstractions for managing asynchronous operations

## Installation

Install MiniAgents using pip:

```
pip install miniagents
```

## Usage

Here's a simple example of defining agents and running them:

```python
from miniagents.miniagents import miniagent, MiniAgents

@miniagent
async def hello_agent(ctx):
    ctx.reply("Hello!")

@miniagent
async def echo_agent(ctx):
    async for msg in ctx.messages:
        ctx.reply(f"You said: {msg}")

async def main():
    async with MiniAgents():
        await achain_loop([
            hello_agent.inquire(),
            echo_agent.inquire()
        ])

if __name__ == "__main__":
    MiniAgents().run(main())
```

This will output:
```
Hello!
You said: Hello!
```

## Documentation

Refer to the docstrings in the source code for detailed documentation on the various classes and functions. Some key concepts:

- `MiniAgents` - The main context manager for running agents
- `miniagent` - Decorator for defining agent functions
- `MessageType` - Union type representing different message formats
- `MessageSequencePromise` - Promise representing a sequence of messages
- `achain_loop` - Utility for chaining agents in a loop

## Examples

The `examples/` directory contains sample code demonstrating how to use MiniAgents for:

- Having conversations with LLMs
- Generating documentation using LLMs
- Implementing self-developing agents

## Contributing

Contributions are welcome! Please submit a pull request or open an issue on GitHub.

## License

MiniAgents is open-source under the MIT License. See LICENSE file for details.
