# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides a simple and flexible way to define agents and their interactions.

## Features

- Define agents as simple Python functions decorated with `@miniagent`
- Agents can send and receive messages asynchronously
- Agents can be chained together to form complex interaction flows
- Built-in support for integrating with language models like OpenAI's GPT and Anthropic's Claude
- Promises and async iterators for handling asynchronous operations and streaming data
- Utilities for joining and splitting message sequences
- Extensible architecture allowing integration with other systems and libraries

## Installation

You can install MiniAgents using pip:

```bash
pip install miniagents
```

## Usage

Here's a simple example of defining an agent and running it:

```python
from miniagents import miniagent, MiniAgents

@miniagent
async def hello_agent(ctx):
    ctx.reply("Hello, world!")

async def main():
    async with MiniAgents():
        hello_agent.inquire()

if __name__ == "__main__":
    MiniAgents().run(main())
```

For more advanced usage, see the examples in the `examples/` directory.

## Integrations

MiniAgents provides built-in support for integrating with language models:

- OpenAI's GPT models via the `openai` package
- Anthropic's Claude models via the `anthropic` package

You can define agents that use these language models to generate responses. See `examples/llm_example.py` for an example.

## Concepts

Some key concepts in MiniAgents:

- `MiniAgent` - A wrapper around a Python function that allows it to send and receive messages
- `Message` - Represents a message that can be sent between agents, with optional metadata
- `MessagePromise` - A promise of a message that can be streamed token by token
- `MessageSequencePromise` - A promise of a sequence of messages that can be streamed message by message
- `StreamAppender` - Allows appending pieces to a streamed promise
- `PromisingContext` - Manages the lifecycle and configuration of promises

## Contributing

Contributions are welcome! Please see the contributing guide for details.

## License

MiniAgents is released under the MIT License. See LICENSE for details.
