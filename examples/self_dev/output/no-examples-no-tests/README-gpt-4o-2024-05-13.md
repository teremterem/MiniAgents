# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of agents that interact with language models and other asynchronous systems. It provides a structured way to handle message passing, streaming, and promise-based asynchronous programming.

## Features

- **Agent-based architecture**: Define agents with specific functions and interact with them using a simple API.
- **Integration with language models**: Built-in support for OpenAI and Anthropic language models.
- **Promise-based asynchronous programming**: Use promises to handle asynchronous operations and streaming data.
- **Message handling**: Define and manage messages between agents with ease.
- **Utilities for common tasks**: Includes utilities for joining and splitting messages, chaining agent interactions, and more.

## Installation

To install MiniAgents, you can use [Poetry](https://python-poetry.org/):

```sh
poetry add miniagents
```

## Usage

### Creating an Agent

You can create an agent by defining a function and decorating it with `@miniagent`:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext, **kwargs):
    # Your agent logic here
    ctx.reply("Hello from my agent!")
```

### Interacting with Agents

To interact with an agent, you can use the `inquire` method:

```python
from miniagents.miniagents import MiniAgents

async def main():
    agent = my_agent
    response = await agent.inquire("Hello, agent!")
    print(await response.aresolve_messages())

miniagents = MiniAgents()
miniagents.run(main())
```

### Integrating with Language Models

MiniAgents provides built-in support for OpenAI and Anthropic language models. You can create agents for these models using the provided functions:

```python
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.ext.llm.anthropic import create_anthropic_agent

openai_agent = create_openai_agent()
anthropic_agent = create_anthropic_agent()
```

### Handling Messages

MiniAgents provides a `Message` class and related utilities to handle messages between agents:

```python
from miniagents.messages import Message

class MyMessage(Message):
    text: str

message = MyMessage(text="Hello, world!")
print(message.serialize())
```

### Utilities

MiniAgents includes several utility functions for common tasks:

- **Joining messages**: Combine multiple messages into a single message.

  ```python
  from miniagents.utils import join_messages

  combined_message = join_messages(["Hello", "world!"])
  ```

- **Splitting messages**: Split a message into multiple messages based on a delimiter.

  ```python
  from miniagents.utils import split_messages

  split_message = split_messages("Hello\n\nworld!")
  ```

- **Chaining agent interactions**: Chain multiple agent interactions in a loop.

  ```python
  from miniagents.utils import achain_loop, AWAIT

  async def main():
      await achain_loop([agent1, AWAIT, agent2])

  miniagents.run(main())
  ```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## Author

Oleksandr Tereshchenko - [toporok@gmail.com](mailto:toporok@gmail.com)

## Acknowledgements

Special thanks to the developers of the libraries and tools that made this project possible.
