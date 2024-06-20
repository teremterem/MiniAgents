# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of interactive agents. It provides abstractions for chat history management, integration with large language models (LLMs) like OpenAI and Anthropic, and utilities for chaining and looping agent interactions.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
  - [MiniAgent](#miniagent)
  - [InteractionContext](#interactioncontext)
  - [Message](#message)
  - [ChatHistory](#chathistory)
- [Extensions](#extensions)
  - [Console User Agent](#console-user-agent)
  - [LLM Integrations](#llm-integrations)
- [Utilities](#utilities)
- [Advanced Usage](#advanced-usage)
- [Contributing](#contributing)
- [License](#license)

## Installation

To install MiniAgents, clone the repository and install the dependencies:

```bash
git clone https://github.com/yourusername/miniagents.git
cd miniagents
pip install -r requirements.txt
```

## Quick Start

Here's a quick example to get you started with MiniAgents:

```python
import asyncio
from miniagents.miniagents import MiniAgents, miniagent
from miniagents.ext.console_user_agent import create_console_user_agent
from miniagents.ext.llm.openai import create_openai_agent

# Define your OpenAI API key
OPENAI_API_KEY = "your-openai-api-key"

# Create an OpenAI agent
openai_agent = create_openai_agent(api_key=OPENAI_API_KEY, model="gpt-3.5-turbo")

# Create a console user agent
user_agent = create_console_user_agent()

# Define a simple interaction loop
async def main():
    async with MiniAgents():
        await user_agent.inquire("Hello, how can I assist you today?")
        response = await openai_agent.inquire("Tell me a joke.")
        print(response)

# Run the interaction loop
asyncio.run(main())
```

## Core Concepts

### MiniAgent

A `MiniAgent` is a wrapper for an agent function that allows calling the agent. You can create a MiniAgent using the `@miniagent` decorator.

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext):
    ctx.reply("Hello, I am a MiniAgent!")
```

### InteractionContext

`InteractionContext` provides the context in which an agent operates. It includes the messages received by the agent and a method to send replies.

### Message

The `Message` class represents a message that can be sent between agents. It supports streaming and promises for asynchronous operations.

### ChatHistory

`ChatHistory` is an abstract class for managing chat history. It provides methods to load and log chat history.

## Extensions

### Console User Agent

The console user agent reads user input from the console and writes back to the console. It also keeps track of the chat history.

```python
from miniagents.ext.console_user_agent import create_console_user_agent

user_agent = create_console_user_agent()
```

### LLM Integrations

MiniAgents supports integration with large language models like OpenAI and Anthropic.

#### OpenAI

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent(api_key="your-openai-api-key", model="gpt-3.5-turbo")
```

#### Anthropic

```python
from miniagents.ext.llm.anthropic import create_anthropic_agent

anthropic_agent = create_anthropic_agent(api_key="your-anthropic-api-key", model="claude-v1")
```

## Utilities

MiniAgents provides several utility functions to facilitate agent interactions.

### `adialog_loop`

Runs a loop that chains the user agent and the assistant agent in a dialog.

```python
from miniagents.utils import adialog_loop

await adialog_loop(user_agent, openai_agent)
```

### `achain_loop`

Runs a loop that chains multiple agents together.

```python
from miniagents.utils import achain_loop

await achain_loop([user_agent, openai_agent])
```

### `join_messages`

Joins multiple messages into a single message using a delimiter.

```python
from miniagents.utils import join_messages

joined_message = join_messages(["Hello", "World"], delimiter=" ")
```

### `split_messages`

Splits a message into multiple messages based on a delimiter.

```python
from miniagents.utils import split_messages

split_message = split_messages("Hello\n\nWorld", delimiter="\n\n")
```

## Advanced Usage

For advanced usage, refer to the source code and the docstrings provided in each module. The framework is designed to be extensible and customizable to fit various use cases.

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
