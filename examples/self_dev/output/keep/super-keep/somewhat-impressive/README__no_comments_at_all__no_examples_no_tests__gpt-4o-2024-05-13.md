# MiniAgents

MiniAgents is a lightweight Python framework designed to facilitate the creation and management of interactive agents. It provides a structured way to define, interact with, and manage agents that can communicate with various Large Language Models (LLMs) such as OpenAI and Anthropic.

## Features

- **Agent Management**: Easily create and manage multiple agents.
- **LLM Integration**: Seamless integration with popular LLMs like OpenAI and Anthropic.
- **Message Handling**: Structured message handling and streaming.
- **Promise-based Architecture**: Efficient handling of asynchronous operations using promises.
- **Extensible**: Easily extendable to support additional LLMs and custom functionalities.

## Installation

To install MiniAgents, you can use [Poetry](https://python-poetry.org/):

```sh
poetry install
```

## Usage

### Creating an Agent

You can create an agent using the `miniagent` decorator. Here is an example of how to create a simple agent:

```python
from miniagents.miniagents import miniagent, MiniAgents

@miniagent
async def my_agent(ctx):
    ctx.reply("Hello, I am your agent!")

# Running the agent
mini_agents = MiniAgents()
mini_agents.run(my_agent.inquire())
```

### Integrating with OpenAI

To create an agent that interacts with OpenAI, you can use the `create_openai_agent` function:

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent()

# Running the OpenAI agent
mini_agents.run(openai_agent.inquire("Hello, OpenAI!"))
```

### Integrating with Anthropic

Similarly, you can create an agent that interacts with Anthropic:

```python
from miniagents.ext.llm.anthropic import create_anthropic_agent

anthropic_agent = create_anthropic_agent()

# Running the Anthropic agent
mini_agents.run(anthropic_agent.inquire("Hello, Anthropic!"))
```

### Handling Messages

MiniAgents provides a structured way to handle messages. You can define different types of messages such as `UserMessage`, `SystemMessage`, and `AssistantMessage`:

```python
from miniagents.ext.llm.llm_common import UserMessage, SystemMessage, AssistantMessage

user_message = UserMessage(text="Hello!")
system_message = SystemMessage(text="System message")
assistant_message = AssistantMessage(text="Assistant message")
```

### Advanced Usage

For more advanced usage, you can leverage the promise-based architecture to handle asynchronous operations efficiently. Here is an example of how to use promises:

```python
from miniagents.messages import MessagePromise

async def my_async_function():
    promise = MessagePromise()
    result = await promise
    print(result)

mini_agents.run(my_async_function())
```

## Configuration

You can configure various aspects of the framework using the `pyproject.toml` file. Here is an example configuration:

```toml
[tool.black]
line-length = 119

[tool.coverage.run]
branch = true

[tool.poetry]
name = "miniagents"
version = "0.0.12"
description = "TODO Oleksandr"
authors = ["Oleksandr Tereshchenko <toporok@gmail.com>"]
homepage = "https://github.com/teremterem/MiniAgents"
readme = "README.md"
license = "MIT"

[tool.poetry.dependencies]
python = ">=3.9,<4.0"
pydantic = ">=2.0.0,<3.0.0"

[tool.poetry.dev-dependencies]
anthropic = "*"
black = "*"
ipython = "*"
jupyterlab = "*"
notebook = "*"
openai = "*"
pre-commit = "*"
pylint = "*"
pytest = "*"
pytest-asyncio = "*"
pytest-cov = "*"
python-dotenv = "*"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on the [GitHub repository](https://github.com/teremterem/MiniAgents).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to Oleksandr Tereshchenko for creating and maintaining this project.
