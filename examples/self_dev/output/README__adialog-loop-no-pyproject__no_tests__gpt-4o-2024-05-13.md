# MiniAgents Framework

MiniAgents is a Python framework designed to facilitate the creation and management of conversational agents. It provides a structured way to handle interactions between users and large language models (LLMs) such as OpenAI's GPT and Anthropic's Claude. The framework is built with flexibility and extensibility in mind, allowing developers to easily integrate different components and customize their behavior.

## Features

- **Agent Management**: Define and manage agents that can handle user interactions and generate responses.
- **Chat History**: Store and manage chat history in various formats, including in-memory and markdown files.
- **LLM Integration**: Seamlessly integrate with popular LLMs like OpenAI and Anthropic.
- **Message Handling**: Stream and process messages token by token, allowing for real-time interaction.
- **Utility Functions**: A set of utility functions to facilitate common tasks such as chaining agents and joining messages.

## Installation

To install the MiniAgents framework, you can use pip:

```bash
pip install miniagents
```

## Getting Started

Here is a simple example to get you started with the MiniAgents framework:

### Example: Simple Conversation

```python
"""
A simple conversation example using the MiniAgents framework.
"""

import logging
from dotenv import load_dotenv
from miniagents.ext.chat_history_md import ChatHistoryMD
from miniagents.ext.console_user_agent import create_console_user_agent
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.miniagents import MiniAgents
from miniagents.utils import adialog_loop

load_dotenv()

async def amain() -> None:
    """
    The main conversation loop.
    """
    chat_history = ChatHistoryMD("CHAT.md")
    try:
        print()
        await adialog_loop(
            user_agent=create_console_user_agent(chat_history=chat_history),
            assistant_agent=create_openai_agent(model="gpt-4o-2024-05-13"),
        )
    except KeyboardInterrupt:
        print()

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    MiniAgents().run(amain())
```

### Example: Using LLMs

```python
"""
Code example for using LLMs.
"""

from pprint import pprint
from dotenv import load_dotenv
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.messages import Message
from miniagents.miniagents import MiniAgents

load_dotenv()

llm_agent = create_openai_agent(model="gpt-4o-2024-05-13")

mini_agents = MiniAgents()

@mini_agents.on_persist_message
async def persist_message(_, message: Message) -> None:
    """
    Print the message to the console.
    """
    print("HASH KEY:", message.hash_key)
    print(type(message).__name__)
    pprint(message.serialize(), width=119)
    print()

async def amain() -> None:
    """
    Send a message to the LLM and print the response.
    """
    reply_sequence = llm_agent.inquire(
        "How are you today?",
        max_tokens=1000,
        temperature=0.0,
        system="Respond only in Yoda-speak.",
    )

    print()
    async for msg_promise in reply_sequence:
        async for token in msg_promise:
            print(f"\033[92;1m{token}\033[0m", end="", flush=True)
        print()
        print()

if __name__ == "__main__":
    mini_agents.run(amain())
```

## Documentation

### Core Concepts

- **MiniAgents**: The main class that manages the lifecycle of agents and their interactions.
- **Agents**: Functions decorated with `@miniagent` that handle specific tasks or interactions.
- **Messages**: The primary data structure for communication between agents.
- **Chat History**: Abstractions for storing and retrieving chat history.

### Modules

- `miniagents`: Core classes and functions.
- `miniagents.ext`: Extensions for integrating with external services and libraries.
- `miniagents.promising`: Classes and functions for handling promises and asynchronous operations.
- `miniagents.utils`: Utility functions for common tasks.

### Extending MiniAgents

You can extend the functionality of MiniAgents by creating custom agents, message types, and chat history handlers. The framework is designed to be modular and flexible, allowing you to integrate it with various services and customize its behavior to fit your needs.

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request on the GitHub repository.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the developers and contributors of the libraries and tools that made this framework possible.

---

This README provides an overview of the MiniAgents framework, its features, and how to get started with it. For more detailed documentation and examples, please refer to the source code and the provided examples.
