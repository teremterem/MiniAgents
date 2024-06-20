# MiniAgents

MiniAgents is an asynchronous framework for building LLM-based multi-agent systems in Python, with a focus on immutable messages and token streaming.

## Features

- **Asynchronous**: Built with asyncio for high performance and scalability.
- **LLM Integration**: Easily integrate with large language models like OpenAI and Anthropic.
- **Immutable Messages**: Ensures message integrity and consistency.
- **Token Streaming**: Supports token-by-token streaming for real-time applications.

## Installation

To install MiniAgents, you can use [Poetry](https://python-poetry.org/):

```sh
poetry add miniagents
```

## Getting Started

### Simple Conversation Example

Here's a simple example to get you started with a conversation using the MiniAgents framework.

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
    # logging.getLogger("miniagents.ext.llm").setLevel(logging.DEBUG)

    MiniAgents().run(amain())
```

### Using LLMs

Here's an example of how to use large language models with MiniAgents.

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

# logging.basicConfig(level=logging.DEBUG)

# llm_agent = create_anthropic_agent(model="claude-3-haiku-20240307")  # claude-3-opus-20240229
llm_agent = create_openai_agent(model="gpt-4o-2024-05-13")  # gpt-3.5-turbo-0125

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
    Send a message to Claude and print the response.
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

- **MiniAgents**: The main class for managing the context of promises and handling the lifecycle of agents.
- **Messages**: Immutable messages that can be sent between agents.
- **Promises**: Represent asynchronous operations that can be resolved in the future.
- **Token Streaming**: Supports streaming tokens for real-time applications.

### Modules

- `miniagents`: Core classes and utilities.
- `miniagents.ext`: Extensions for integrating with external services like OpenAI and Anthropic.
- `miniagents.promising`: Classes and utilities for handling promises and asynchronous operations.

### Examples

- `examples/conversation.py`: A simple conversation example.
- `examples/llm_example.py`: Example of using large language models.
- `examples/self_dev`: Self-development examples and utilities.

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the contributors and the open-source community for their support and contributions.

## Contact

For any questions or inquiries, please contact Oleksandr Tereshchenko at [toporok@gmail.com](mailto:toporok@gmail.com).

---

Happy coding with MiniAgents! 🚀
