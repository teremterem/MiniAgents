# MiniAgents

MiniAgents is a Python framework for building multi-agent systems with a focus on natural language processing and large language models (LLMs).

## Features

- Abstractions for defining agents and their interactions
- Built-in support for popular LLMs like OpenAI's GPT models and Anthropic's Claude
- Asynchronous streaming of agent messages and LLM responses
- Flexible chat history management, including in-memory and Markdown-based persistence
- Promises-based programming model for handling asynchronous operations
- Immutable data structures for message passing between agents
- Utilities for common interaction patterns like dialog loops and agent chaining

## Installation

```bash
pip install miniagents
```

## Basic Usage

Here's a simple example of using MiniAgents to create a dialog between a user and an AI assistant powered by OpenAI's GPT-3.5-turbo model:

```python
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.ext.console_user_agent import create_console_user_agent
from miniagents.utils import adialog_loop

async def main():
    user_agent = create_console_user_agent()
    assistant_agent = create_openai_agent(model="gpt-3.5-turbo")

    await adialog_loop(user_agent, assistant_agent)

asyncio.run(main())
```

This will start an interactive dialog where the user can chat with the AI assistant in the console.

## Documentation

For more details on using MiniAgents, please refer to the source code which is extensively documented with docstrings. A full API reference and user guide are planned for the future.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on the [GitHub repository](https://github.com/yourusername/miniagents).

## License

MiniAgents is open-source software licensed under the [MIT license](https://opensource.org/licenses/MIT).
