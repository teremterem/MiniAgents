# MiniAgents

MiniAgents is an asynchronous framework for building LLM-based multi-agent systems in Python, with a focus on immutable messages and token streaming. It provides a structured way to create, manage, and interact with multiple agents, each capable of handling specific tasks or roles within a larger system.

## Features

- **Asynchronous Execution**: Leverage Python's `asyncio` for efficient, non-blocking operations.
- **Immutable Messages**: Ensure data integrity and consistency with immutable message objects.
- **Token Streaming**: Stream tokens from large language models (LLMs) for real-time interaction.
- **Extensible**: Easily integrate with various LLM providers like OpenAI and Anthropic.
- **Chat History Management**: Maintain and manage chat histories with different storage backends.
- **Agent Chaining**: Chain multiple agents together to create complex workflows.

## Installation

To install MiniAgents, you can use `poetry`:

```sh
poetry add miniagents
```

Or, if you prefer `pip`:

```sh
pip install miniagents
```

## Getting Started

### Basic Example

Here's a simple example to get you started with MiniAgents. This example demonstrates a basic conversation loop between a user and an assistant agent using OpenAI's GPT-4 model.

```python
import logging
from dotenv import load_dotenv
from miniagents.ext.chat_history_md import ChatHistoryMD
from miniagents.ext.console_user_agent import create_console_user_agent
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.miniagents import MiniAgents
from miniagents.utils import adialog_loop

load_dotenv()

async def amain() -> None:
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

### Using LLMs

You can also directly interact with LLMs. Here's an example of sending a message to an LLM and printing the response.

```python
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
    print("HASH KEY:", message.hash_key)
    print(type(message).__name__)
    pprint(message.serialize(), width=119)
    print()

async def amain() -> None:
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

## Advanced Usage

### Self-Developer Example

MiniAgents can also be used for more complex tasks, such as self-developing agents that produce documentation for the framework itself.

```python
import asyncio
import logging
from pathlib import Path
from typing import Union
from examples.self_dev.self_dev_common import MODEL_AGENTS, SELF_DEV_OUTPUT, SKIPS_FOR_REPO_VARIATIONS, FullRepoMessage
from examples.self_dev.self_dev_prompts import GLOBAL_SYSTEM_HEADER, PRODUCE_README_SYSTEM_FOOTER
from miniagents.ext.llm.llm_common import SystemMessage
from miniagents.miniagents import miniagent, MiniAgents, InteractionContext

@miniagent
async def readme_agent(_) -> None:
    experiment_name = input("\nEnter experiment folder name: ")
    experiment_name = "_".join(experiment_name.lower().split())
    if not experiment_name:
        experiment_name = "DEFAULT"

    for variation_idx, (variation_name, variation_skips) in enumerate(SKIPS_FOR_REPO_VARIATIONS.items()):
        for model_idx, (model, model_agent) in enumerate(MODEL_AGENTS.items()):
            md_file = SELF_DEV_OUTPUT / f"README__{experiment_name}__{variation_name}__{model}.md"
            if md_file.exists() and md_file.stat().st_size > 0 and md_file.read_text(encoding="utf-8").strip():
                continue

            echo_agent.inquire(
                file_agent.inquire(
                    model_agent.inquire(
                        [
                            SystemMessage(GLOBAL_SYSTEM_HEADER),
                            FullRepoMessage(
                                experiment_name=experiment_name,
                                variation_name=variation_name,
                                skip_if_starts_with=variation_skips,
                            ),
                            SystemMessage(PRODUCE_README_SYSTEM_FOOTER),
                        ],
                        temperature=0,
                    ),
                    file=str(md_file),
                ),
                color=f"{90 + len(MODEL_AGENTS) * variation_idx + model_idx};1",
            )

async def amain() -> None:
    async with MiniAgents():
        readme_agent.inquire()
    print("Readme file(s) produced\n")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("miniagents.ext.llm").setLevel(logging.DEBUG)
    asyncio.run(amain())
```

## Testing

MiniAgents comes with a comprehensive test suite. To run the tests, you can use `pytest`:

```sh
pytest
```

## Contributing

Contributions are welcome! Please read the [CONTRIBUTING.md](https://github.com/teremterem/MiniAgents/blob/main/CONTRIBUTING.md) for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/teremterem/MiniAgents/blob/main/LICENSE) file for details.

## Acknowledgements

Special thanks to the contributors and the open-source community for their invaluable support and contributions.

---

For more information, visit the [MiniAgents GitHub repository](https://github.com/teremterem/MiniAgents).
