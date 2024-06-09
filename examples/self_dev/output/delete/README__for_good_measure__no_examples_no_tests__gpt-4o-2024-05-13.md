# MiniAgents

MiniAgents is a Python framework designed to facilitate the integration and interaction of various language models and agents. It provides a structured way to create, manage, and interact with agents, allowing for seamless communication and data exchange between them.

## Features

- **Integration with Language Models**: Easily integrate with popular language models like OpenAI and Anthropic.
- **Promise-based Architecture**: Utilize promises for asynchronous operations, ensuring smooth and efficient task management.
- **Streaming Support**: Stream data and messages between agents, allowing for real-time interactions.
- **Extensible and Modular**: Designed to be easily extendable, allowing developers to add new functionalities and integrations.

## Installation

To install MiniAgents, you can use [Poetry](https://python-poetry.org/):

```sh
poetry add miniagents
```

## Usage

### Creating an Agent

You can create an agent using the `miniagent` decorator. Here's an example of how to create a simple agent:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext, **kwargs):
    # Your agent logic here
    ctx.reply("Hello, world!")
```

### Integrating with OpenAI

To create an agent that integrates with OpenAI, you can use the `create_openai_agent` function:

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent()
```

### Running the Framework

To run the framework, you can use the `MiniAgents` context manager:

```python
from miniagents.miniagents import MiniAgents

async def main():
    async with MiniAgents() as context:
        # Your code here

MiniAgents().run(main())
```

## Advanced Features

### Streaming Messages

MiniAgents supports streaming messages between agents. This allows for real-time interactions and data exchange. You can use the `StreamAppender` and `StreamedPromise` classes to handle streaming data.

### Handling Errors

Different Promise and StreamedPromise resolvers, piece streamers, appenders, and other components should always catch `BaseExceptions` and not just `Exceptions`. This ensures that errors are properly propagated and handled, preventing issues like hanging promises.

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request on [GitHub](https://github.com/teremterem/MiniAgents).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to Oleksandr Tereshchenko for developing and maintaining this framework.

## TODO

- [ ] Complete the documentation for all classes and functions.
- [ ] Add more examples and use cases.
- [ ] Improve test coverage and add more unit tests.

## Things to remember (for the developer of this framework)

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders and what not should always catch
  BaseExceptions and not just Exceptions** when they capture errors to pass those errors as "pieces" in order for
  those errors to be raised at the "consumer side". This is because many of the aforementioned Promising "primitives"
  are often part of mechanisms that involve communications between async tasks via asyncio.Queue objects and just
  interrupting those promises with KeyboardInterrupt which are extended from BaseException instead of letting
  KeyboardInterrupt to go through the queue leads to hanging of those promises (a queue is waiting for END_OF_QUEUE
  sentinel forever but the task that should send it is dead).
