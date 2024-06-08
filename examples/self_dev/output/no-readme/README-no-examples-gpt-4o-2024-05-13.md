# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of agents that interact with language models (LLMs) and other services. It provides a structured way to define, run, and manage agents, making it easier to build complex systems that require asynchronous interactions and message passing.

## Features

- **Agent Management**: Define and manage agents with ease using decorators.
- **Asynchronous Interactions**: Support for asynchronous message passing and interaction handling.
- **LLM Integration**: Built-in support for integrating with popular language models like OpenAI and Anthropic.
- **Message Handling**: Structured message classes and promises for handling asynchronous message streams.
- **Error Handling**: Robust error handling and logging mechanisms.
- **Utilities**: Various utility functions to facilitate common tasks like message joining and splitting.

## Installation

To install MiniAgents, you can use [Poetry](https://python-poetry.org/):

```sh
poetry add miniagents
```

## Quick Start

### Defining an Agent

You can define an agent using the `@miniagent` decorator. An agent is essentially an asynchronous function that interacts with other agents or services.

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext) -> None:
    ctx.reply("Hello, I am an agent!")
```

### Running an Agent

To run an agent, you need to create an instance of `MiniAgents` and use the `inquire` method to send messages to the agent.

```python
from miniagents.miniagents import MiniAgents

async def main():
    async with MiniAgents():
        response = await my_agent.inquire("Hello, agent!").aresolve_messages()
        for message in response:
            print(message.text)

import asyncio
asyncio.run(main())
```

### Integrating with Language Models

MiniAgents provides built-in support for integrating with popular language models like OpenAI and Anthropic.

#### OpenAI Integration

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent(model="gpt-3.5-turbo")

async def main():
    async with MiniAgents():
        response = await openai_agent.inquire("Tell me a joke.").aresolve_messages()
        for message in response:
            print(message.text)

import asyncio
asyncio.run(main())
```

#### Anthropic Integration

```python
from miniagents.ext.llm.anthropic import create_anthropic_agent

anthropic_agent = create_anthropic_agent(model="claude-3")

async def main():
    async with MiniAgents():
        response = await anthropic_agent.inquire("Tell me a joke.").aresolve_messages()
        for message in response:
            print(message.text)

import asyncio
asyncio.run(main())
```

## Advanced Usage

### Message Handling

MiniAgents provides a structured way to handle messages using the `Message` class and its derivatives.

```python
from miniagents.messages import Message

class CustomMessage(Message):
    custom_field: str

message = CustomMessage(text="Hello", custom_field="Custom Value")
print(message.text)  # Output: Hello
print(message.custom_field)  # Output: Custom Value
```

### Error Handling

MiniAgents includes robust error handling mechanisms to ensure that your agents can handle exceptions gracefully.

```python
from miniagents.promising.errors import PromisingError

try:
    # Your code here
except PromisingError as e:
    print(f"An error occurred: {e}")
```

### Utilities

MiniAgents provides various utility functions to facilitate common tasks.

#### Joining Messages

```python
from miniagents.utils import join_messages

async def main():
    messages = ["Hello", "World"]
    joined_message = await join_messages(messages).aresolve()
    print(joined_message.text)  # Output: Hello\n\nWorld

import asyncio
asyncio.run(main())
```

#### Splitting Messages

```python
from miniagents.utils import split_messages

async def main():
    message = "Hello\n\nWorld"
    split_message = await split_messages(message).aresolve_messages()
    for msg in split_message:
        print(msg.text)

import asyncio
asyncio.run(main())
```

## Testing

MiniAgents includes a comprehensive test suite to ensure the reliability of the framework. You can run the tests using `pytest`.

```sh
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on GitHub.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the contributors and the open-source community for their support and contributions.

---

For more information, please visit the [GitHub repository](https://github.com/teremterem/MiniAgents).
