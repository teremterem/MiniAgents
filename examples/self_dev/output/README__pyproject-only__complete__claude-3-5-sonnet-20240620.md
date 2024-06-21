# MiniAgents

MiniAgents is an asynchronous framework for building LLM-based multi-agent systems in Python, with a focus on immutable messages and token streaming.

## Features

- Asynchronous design for efficient handling of multiple agents
- Support for immutable messages to ensure data integrity
- Token streaming capabilities for real-time processing
- Integration with popular LLM providers (OpenAI, Anthropic)
- Flexible agent creation and interaction
- Built-in chat history management
- Extensible architecture for custom agent implementations

## Installation

You can install MiniAgents using pip:

```
pip install miniagents
```

## Quick Start

Here's a simple example of how to use MiniAgents:

```python
from miniagents.ext.chat_history_md import ChatHistoryMD
from miniagents.ext.console_user_agent import create_console_user_agent
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.miniagents import MiniAgents
from miniagents.utils import adialog_loop

async def amain():
    chat_history = ChatHistoryMD("chat_history.md")
    await adialog_loop(
        user_agent=create_console_user_agent(chat_history=chat_history),
        assistant_agent=create_openai_agent(model="gpt-4"),
    )

if __name__ == "__main__":
    MiniAgents().run(amain())
```

This example sets up a simple conversation loop between a console user and an OpenAI-powered assistant.

## Key Components

- `MiniAgents`: The main class for managing the context of promises and agent interactions.
- `miniagent`: A decorator for creating agent functions.
- `Message`: A class representing immutable messages exchanged between agents.
- `ChatHistory`: An abstract class for managing chat history.
- `StreamedPromise`: A class representing a promise of a whole value that can be streamed piece by piece.

## Advanced Usage

MiniAgents supports complex multi-agent systems, custom LLM integrations, and advanced message handling. Check the `examples` directory for more sophisticated use cases.

## Contributing

Contributions to MiniAgents are welcome! Please refer to the project's GitHub repository for contribution guidelines.

## License

MiniAgents is released under the MIT License. See the LICENSE file for details.

## Documentation

For more detailed information on using MiniAgents, please refer to the inline documentation in the source code. Each module and major class contains docstrings explaining their purpose and usage.

## Support

If you encounter any issues or have questions, please file an issue on the GitHub repository.

---

This README provides a high-level overview of the MiniAgents framework, including its key features, installation instructions, a quick start guide, and information about its main components. You may want to expand on certain sections or add more examples as the framework evolves.
