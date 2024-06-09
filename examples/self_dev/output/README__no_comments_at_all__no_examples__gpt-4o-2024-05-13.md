# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of mini agents that interact with large language models (LLMs) such as OpenAI and Anthropic. The framework provides a structured way to define, run, and manage interactions with these agents, making it easier to build complex conversational systems.

## Features

- **Agent Management**: Define and manage multiple agents with ease.
- **LLM Integration**: Seamless integration with OpenAI and Anthropic LLMs.
- **Message Handling**: Structured message handling and serialization.
- **Promise-Based Architecture**: Use promises to handle asynchronous operations and streaming data.
- **Extensible**: Easily extend the framework to support additional LLMs or custom functionalities.

## Installation

To install MiniAgents, you can use `pip`:

```bash
pip install miniagents
```

## Quick Start

### Define an Agent

You can define an agent using the `@miniagent` decorator. Here's an example of a simple agent:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def echo_agent(ctx: InteractionContext) -> None:
    async for message in ctx.messages:
        ctx.reply(message)
```

### Create an LLM Agent

You can create an agent that interacts with an LLM, such as OpenAI or Anthropic:

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent(model="gpt-3.5-turbo")
```

### Run the Agent

To run the agent, you can use the `MiniAgents` context manager:

```python
from miniagents.miniagents import MiniAgents, Message

async def main():
    async with MiniAgents():
        response = await openai_agent.inquire(Message(text="Hello, how are you?"))
        print(await response.aresolve_messages())

import asyncio
asyncio.run(main())
```

## Advanced Usage

### Handling Streams

MiniAgents supports streaming responses from LLMs. You can handle streaming tokens as follows:

```python
async def handle_streaming():
    async with MiniAgents():
        response = openai_agent.inquire(Message(text="Tell me a story."), stream=True)
        async for msg_promise in response:
            async for token in msg_promise:
                print(token, end='')

asyncio.run(handle_streaming())
```

### Custom Message Types

You can define custom message types by extending the `Message` class:

```python
from miniagents.messages import Message

class CustomMessage(Message):
    custom_field: str

custom_message = CustomMessage(text="Hello", custom_field="example")
```

### Error Handling

MiniAgents provides robust error handling mechanisms. You can define custom error handlers for promises and message streams.

## Testing

MiniAgents includes a comprehensive test suite. To run the tests, you can use `pytest`:

```bash
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on GitHub.

## License

MiniAgents is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

## Acknowledgements

Special thanks to the developers and contributors of the libraries and tools that made this framework possible.

## Contact

For any questions or inquiries, please contact Oleksandr Tereshchenko at [toporok@gmail.com](mailto:toporok@gmail.com).

---

Happy coding with MiniAgents! 🚀
