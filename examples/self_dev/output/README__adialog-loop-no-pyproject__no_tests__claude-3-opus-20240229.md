# MiniAgents

MiniAgents is a Python framework for building multi-agent systems and working with large language models (LLMs).

## Features

- Abstractions for defining agents and their interactions
- Support for streaming responses from LLMs token by token
- Built-in integrations with OpenAI and Anthropic LLMs
- Utilities for managing chat history and working with markdown files
- Promising library for handling asynchronous operations and data flows

## Installation

TODO: Provide installation instructions once the package is available on PyPI or other package repositories.

## Usage

### Defining Agents

Agents in MiniAgents are defined using the `@miniagent` decorator. Here's an example:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def echo_agent(ctx: InteractionContext) -> None:
    ctx.reply(ctx.messages)
```

### Interacting with LLMs

MiniAgents provides integrations with OpenAI and Anthropic LLMs. Here's an example of using OpenAI's GPT-4:

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent(model="gpt-4")

response = openai_agent.inquire("What is the capital of France?")
```

### Managing Chat History

MiniAgents includes utilities for managing chat history, such as the `ChatHistoryMD` class for working with markdown files:

```python
from miniagents.ext.chat_history_md import ChatHistoryMD

chat_history = ChatHistoryMD("chat.md")
await chat_history.aload_chat_history()
```

### Promising Library

MiniAgents includes the Promising library, which provides abstractions for handling asynchronous operations and data flows. Here's an example of using a `StreamedPromise`:

```python
from miniagents.promising.promising import StreamedPromise

async def token_streamer():
    yield "Hello"
    yield "World"

promise = StreamedPromise(streamer=token_streamer)

async for token in promise:
    print(token)
```

## Examples

The `examples` directory contains various examples demonstrating how to use MiniAgents, including:

- `conversation.py`: A simple conversation example using the MiniAgents framework
- `llm_example.py`: Code example for using LLMs with MiniAgents
- `self_dev`: Examples related to self-development and documentation generation for the MiniAgents framework itself

## Contributing

Contributions to MiniAgents are welcome! If you find a bug or have a feature request, please open an issue on the GitHub repository. If you'd like to contribute code, please fork the repository and submit a pull request.

## License

MiniAgents is released under the MIT License. See the `LICENSE` file for more information.
