# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of agents that interact with language models (LLMs) and other services. It provides a structured way to define, call, and manage agents, making it easier to build complex systems that rely on asynchronous interactions and streaming data.

## Features

- **Agent Management**: Define and manage agents with ease using decorators and classes.
- **Asynchronous Interaction**: Support for asynchronous interactions with agents.
- **Streaming**: Stream data token by token or message by message.
- **Integration with LLMs**: Built-in support for integrating with OpenAI and Anthropic language models.
- **Promise-based Architecture**: Use promises to handle asynchronous data and interactions.
- **Utilities**: Various utility functions to handle common tasks like joining and splitting messages.

## Installation

To install MiniAgents, you can use [Poetry](https://python-poetry.org/):

```sh
poetry add miniagents
```

## Quick Start

### Defining an Agent

You can define an agent using the `@miniagent` decorator. Here's an example of a simple agent:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def echo_agent(ctx: InteractionContext, **kwargs):
    async for message in ctx.messages:
        ctx.reply(message)
```

### Creating an Agent for OpenAI

To create an agent that interacts with OpenAI's language model:

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent()
```

### Creating an Agent for Anthropic

To create an agent that interacts with Anthropic's language model:

```python
from miniagents.ext.llm.anthropic import create_anthropic_agent

anthropic_agent = create_anthropic_agent()
```

### Running an Agent

To run an agent and get its response:

```python
from miniagents.miniagents import MiniAgents

async def main():
    async with MiniAgents() as context:
        response = await openai_agent.inquire("Hello, how are you?")
        print(await response.aresolve_messages())

MiniAgents().run(main())
```

## Advanced Usage

### Streaming Responses

MiniAgents supports streaming responses token by token. This can be useful for real-time applications:

```python
async def main():
    async with MiniAgents() as context:
        response = openai_agent.inquire("Tell me a story.")
        async for token in response:
            print(token, end="")

MiniAgents().run(main())
```

### Handling Multiple Agents

You can chain multiple agents together and manage their interactions:

```python
from miniagents.utils import achain_loop, AWAIT

async def main():
    async with MiniAgents() as context:
        await achain_loop(
            agents=[
                openai_agent,
                AWAIT,
                anthropic_agent,
                AWAIT,
            ],
            initial_input="Start the conversation."
        )

MiniAgents().run(main())
```

## Utilities

MiniAgents provides several utility functions to help with common tasks:

- **join_messages**: Join multiple messages into a single message.
- **split_messages**: Split a message into multiple messages based on a delimiter.

Example of joining messages:

```python
from miniagents.utils import join_messages

async def main():
    async with MiniAgents() as context:
        joined_message = join_messages(["Hello", "World"], delimiter=" ")
        print(await joined_message.aresolve())

MiniAgents().run(main())
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on the [GitHub repository](https://github.com/teremterem/MiniAgents).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or inquiries, please contact Oleksandr Tereshchenko at [toporok@gmail.com](mailto:toporok@gmail.com).
