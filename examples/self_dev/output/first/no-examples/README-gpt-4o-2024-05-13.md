# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of asynchronous agents that can interact with each other through messages. The framework supports integration with various language models (LLMs) such as OpenAI and Anthropic, and provides utilities for handling promises, message sequences, and more.

## Features

- **Asynchronous Agent Management**: Create and manage agents that can run in parallel and interact with each other asynchronously.
- **LLM Integration**: Seamlessly integrate with language models from OpenAI and Anthropic.
- **Message Handling**: Define and manage messages that can be sent between agents, including support for nested messages.
- **Promise-Based Architecture**: Utilize promises to handle asynchronous operations and message streaming.
- **Utilities**: Various utility functions to handle message sequences, joining, splitting, and more.

## Installation

To install MiniAgents, you can use `pip`:

```bash
pip install miniagents
```

## Quick Start

### Creating an Agent

You can create an agent using the `@miniagent` decorator:

```python
from miniagents.miniagents import miniagent, MiniAgents

@miniagent
async def my_agent(ctx):
    ctx.reply("Hello from my_agent!")

async def main():
    async with MiniAgents():
        response = await my_agent.inquire()
        print(await response.aresolve_messages())

import asyncio
asyncio.run(main())
```

### Integrating with OpenAI

To create an agent that uses OpenAI's language model:

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent(model="gpt-3.5-turbo")

async def main():
    async with MiniAgents():
        response = await openai_agent.inquire("Hello, OpenAI!")
        print(await response.aresolve_messages())

import asyncio
asyncio.run(main())
```

### Integrating with Anthropic

To create an agent that uses Anthropic's language model:

```python
from miniagents.ext.llm.anthropic import create_anthropic_agent

anthropic_agent = create_anthropic_agent(model="claude-3")

async def main():
    async with MiniAgents():
        response = await anthropic_agent.inquire("Hello, Anthropic!")
        print(await response.aresolve_messages())

import asyncio
asyncio.run(main())
```

## Advanced Usage

### Handling Message Sequences

You can handle sequences of messages using `MessageSequence`:

```python
from miniagents.miniagents import MessageSequence

async def main():
    async with MiniAgents():
        msg_seq = MessageSequence()
        with msg_seq.message_appender:
            msg_seq.message_appender.append("Message 1")
            msg_seq.message_appender.append("Message 2")

        messages = await msg_seq.sequence_promise.aresolve_messages()
        for msg in messages:
            print(msg.text)

import asyncio
asyncio.run(main())
```

### Using Promises

MiniAgents provides a promise-based architecture for handling asynchronous operations:

```python
from miniagents.promising.promising import Promise

async def my_resolver(promise):
    await asyncio.sleep(1)
    return "Resolved Value"

async def main():
    async with MiniAgents():
        my_promise = Promise(resolver=my_resolver)
        result = await my_promise
        print(result)

import asyncio
asyncio.run(main())
```

## Testing

MiniAgents includes a comprehensive test suite. To run the tests, you can use `pytest`:

```bash
pytest
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## Acknowledgements

Special thanks to the developers and contributors of the libraries and tools that made this project possible.

## Contact

For any questions or inquiries, please contact Oleksandr Tereshchenko at [toporok@gmail.com](mailto:toporok@gmail.com).
