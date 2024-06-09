# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides a set of tools and abstractions for defining agents, managing their interactions, and integrating with language models like OpenAI and Anthropic.

## Features

- Define agents as simple Python functions decorated with `@miniagent`
- Agents can send and receive messages asynchronously
- Agents can be chained together to form complex interaction flows
- Built-in integration with OpenAI and Anthropic language models
- Promises and streaming support for handling asynchronous operations
- Utilities for joining and splitting messages

## Installation

You can install MiniAgents using pip:

```
pip install miniagents
```

## Usage

Here's a simple example of defining an agent and running an interaction:

```python
from miniagents import miniagent, MiniAgents

@miniagent
async def hello_agent(ctx):
    ctx.reply("Hello, how can I assist you today?")

async def main():
    async with MiniAgents():
        result = await hello_agent.inquire("Hi there!")
        print(result)

if __name__ == "__main__":
    MiniAgents().run(main())
```

For more detailed usage and examples, please refer to the documentation.

## Documentation

TODO: Add a link to the documentation.

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue on the GitHub repository. If you'd like to contribute code, please fork the repository and submit a pull request.

## License

MiniAgents is released under the MIT License. See the `LICENSE` file for more details.
