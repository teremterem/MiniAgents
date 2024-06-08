# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of agents that interact with language models and other asynchronous tasks. It provides a structured way to handle message passing, promise-based asynchronous operations, and integration with popular language models like OpenAI and Anthropic.

## Features

- **Agent-based architecture**: Define agents with specific functions and manage their interactions.
- **Promise-based asynchronous operations**: Use promises to handle asynchronous tasks and message streaming.
- **Integration with language models**: Easily integrate with OpenAI and Anthropic language models.
- **Message handling**: Define and manage messages between agents with support for streaming and sequence promises.
- **Utility functions**: Various utility functions to facilitate common tasks like message joining and splitting.

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
    ctx.reply("Hello, world!")
```

### Running an Agent

To run an agent, you can use the `MiniAgents` context:

```python
from miniagents.miniagents import MiniAgents

async def main():
    agent = my_agent()
    response = await agent.inquire("Hello!")
    print(await response.aresolve_messages())

miniagents = MiniAgents()
miniagents.run(main())
```

### Integrating with OpenAI

To create an agent that interacts with OpenAI models, use the `create_openai_agent` function:

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent()

async def main():
    response = await openai_agent.inquire("Tell me a joke.")
    print(await response.aresolve_messages())

miniagents.run(main())
```

### Integrating with Anthropic

To create an agent that interacts with Anthropic models, use the `create_anthropic_agent` function:

```python
from miniagents.ext.llm.anthropic import create_anthropic_agent

anthropic_agent = create_anthropic_agent()

async def main():
    response = await anthropic_agent.inquire("Tell me a story.")
    print(await response.aresolve_messages())

miniagents.run(main())
```

## Utility Functions

### Joining Messages

You can join multiple messages into a single message using the `join_messages` function:

```python
from miniagents.utils import join_messages

async def main():
    messages = ["Hello", "world"]
    joined_message = join_messages(messages)
    print(await joined_message.aresolve())

miniagents.run(main())
```

### Splitting Messages

You can split a message into multiple messages using the `split_messages` function:

```python
from miniagents.utils import split_messages

async def main():
    message = "Hello\n\nworld"
    split_message = split_messages(message)
    print(await split_message.aresolve_messages())

miniagents.run(main())
```

## Things to Remember (for the Developer of this Framework)

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders, and whatnot should always catch `BaseExceptions` and not just `Exceptions`** when they capture errors to pass those errors as "pieces" in order for those errors to be raised at the "consumer side". This is because many of the aforementioned Promising "primitives" are often part of mechanisms that involve communications between async tasks via `asyncio.Queue` objects and just interrupting those promises with `KeyboardInterrupt` which are extended from `BaseException` instead of letting `KeyboardInterrupt` to go through the queue leads to hanging of those promises (a queue is waiting for `END_OF_QUEUE` sentinel forever but the task that should send it is dead).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## Authors

- Oleksandr Tereshchenko - [toporok@gmail.com](mailto:toporok@gmail.com)

## Acknowledgments

- [Poetry](https://python-poetry.org/) for dependency management.
- [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation and settings management.
- [OpenAI](https://openai.com/) and [Anthropic](https://www.anthropic.com/) for their language models.
