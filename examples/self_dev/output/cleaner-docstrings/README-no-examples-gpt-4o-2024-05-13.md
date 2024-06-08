# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of agents that interact with language models (LLMs) and other asynchronous tasks. It provides a structured way to define, run, and manage agents, making it easier to build complex systems that rely on asynchronous interactions.

## Features

- **Agent Management**: Define and manage agents using decorators.
- **LLM Integration**: Seamlessly integrate with OpenAI and Anthropic language models.
- **Message Handling**: Handle messages and message sequences with ease.
- **Promise-Based Asynchronous Programming**: Use promises to manage asynchronous tasks and streams.
- **Utilities**: Various utility functions to aid in agent interactions and message handling.

## Installation

To install MiniAgents, you can use `poetry`:

```bash
poetry add miniagents
```

Or, if you prefer `pip`:

```bash
pip install miniagents
```

## Quick Start

### Define an Agent

You can define an agent using the `@miniagent` decorator. An agent is essentially an asynchronous function that interacts with a context.

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext) -> None:
    ctx.reply("Hello, I am an agent!")
```

### Run an Agent

To run an agent, you need to create an instance of `MiniAgents` and use the `inquire` method to send messages to the agent.

```python
from miniagents.miniagents import MiniAgents

async def main():
    async with MiniAgents():
        replies = my_agent.inquire()
        async for reply in replies:
            print(await reply)

import asyncio
asyncio.run(main())
```

### Integrate with LLMs

MiniAgents provides built-in support for OpenAI and Anthropic language models. You can create agents for these models using the provided functions.

```python
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.messages import Message

openai_agent = create_openai_agent(model="gpt-3.5-turbo")

async def main():
    async with MiniAgents():
        replies = openai_agent.inquire(
            Message(text="Hello, how are you?", role="user"),
            system="You are a helpful assistant.",
            max_tokens=50,
            temperature=0.7,
        )
        async for reply in replies:
            print(await reply)

import asyncio
asyncio.run(main())
```

## Advanced Usage

### Handling Message Sequences

MiniAgents allows you to handle sequences of messages, making it easier to manage complex interactions.

```python
from miniagents.miniagents import MessageSequence

async def main():
    async with MiniAgents():
        sequence = MessageSequence.turn_into_sequence_promise([
            "Message 1",
            {"text": "Message 2", "role": "user"},
            Message(text="Message 3", role="assistant")
        ])
        messages = await sequence.aresolve_messages()
        for msg in messages:
            print(msg)

import asyncio
asyncio.run(main())
```

### Using Promises

Promises in MiniAgents are used to manage asynchronous tasks and streams. You can create and handle promises using the provided classes.

```python
from miniagents.promising.promising import Promise

async def my_async_function():
    return "Result"

async def main():
    promise = Promise(resolver=my_async_function)
    result = await promise
    print(result)

import asyncio
asyncio.run(main())
```

## Testing

MiniAgents comes with a comprehensive test suite. You can run the tests using `pytest`.

```bash
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on GitHub.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the developers and contributors of the libraries and tools that made this project possible.

## Contact

For any questions or inquiries, please contact Oleksandr Tereshchenko at [toporok@gmail.com](mailto:toporok@gmail.com).

---

Happy coding with MiniAgents! 🚀
