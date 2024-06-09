# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides a set of tools and abstractions for defining agents, managing their interactions, and integrating with language models like OpenAI and Anthropic.

## Features

- Define agents as simple Python functions decorated with `@miniagent`
- Agents can send and receive messages asynchronously
- Agents can be chained together to form complex interaction flows
- Built-in integration with OpenAI and Anthropic language models
- Extensible architecture to support other language models and backends
- Promise-based API for handling asynchronous operations
- Utilities for joining and splitting message sequences
- Flexible configuration options for customizing agent behavior

## Installation

You can install MiniAgents using pip:

```
pip install miniagents
```

## Usage

Here's a simple example of defining an agent using MiniAgents:

```python
from miniagents import miniagent, InteractionContext

@miniagent
async def hello_agent(ctx: InteractionContext):
    ctx.reply("Hello, world!")
```

To run the agent, you can use the `MiniAgents` context manager:

```python
from miniagents import MiniAgents

async with MiniAgents() as ma:
    result = await hello_agent.inquire()
    print(result)  # Output: Hello, world!
```

For more advanced usage, including chaining agents together and integrating with language models, please refer to the documentation.

## Documentation

TODO: Add a link to the documentation once it's available.

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue on the GitHub repository. If you'd like to contribute code, please fork the repository and submit a pull request.

## License

MiniAgents is released under the MIT License. See the `LICENSE` file for more information.
