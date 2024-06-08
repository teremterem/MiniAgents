# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of agents that interact with large language models (LLMs) and other asynchronous tasks. The framework provides a structured way to define, run, and manage these agents, making it easier to build complex, interactive applications.

## Features

- **Agent Management**: Define and manage agents that can interact with LLMs and other asynchronous tasks.
- **LLM Integration**: Built-in support for integrating with OpenAI and Anthropic language models.
- **Message Handling**: Stream and handle messages between agents efficiently.
- **Promise-Based Architecture**: Use promises to manage asynchronous tasks and streams.
- **Utilities**: Various utility functions to facilitate common tasks like message joining and splitting.

## Installation

To install MiniAgents, you can use `poetry`:

```bash
poetry add miniagents
```

## Usage

### Basic Example

Here's a basic example of how to use MiniAgents to create a conversation loop with an OpenAI agent:

```python
import readline  # pylint: disable=unused-import
from dotenv import load_dotenv
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.miniagent_typing import MessageType
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext
from miniagents.promising.sentinels import AWAIT
from miniagents.utils import achain_loop

load_dotenv()

CHAT_HISTORY: list[MessageType] = []

@miniagent
async def user_agent(ctx: InteractionContext) -> None:
    print("\033[92;1m", end="", flush=True)
    async for msg_promise in ctx.messages:
        print(f"\n{msg_promise.preliminary_metadata.agent_alias}: ", end="", flush=True)
        async for token in msg_promise:
            print(token, end="", flush=True)
        print("\n")

    CHAT_HISTORY.append(ctx.messages)
    print("\033[93;1m", end="", flush=True)
    CHAT_HISTORY.append(input("USER: "))

    ctx.reply(CHAT_HISTORY)

async def amain() -> None:
    try:
        print()
        await achain_loop(
            [
                user_agent,
                AWAIT,
                create_openai_agent(model="gpt-4o-2024-05-13"),
            ]
        )
    except KeyboardInterrupt:
        ...
    finally:
        print("\033[0m\n")

if __name__ == "__main__":
    MiniAgents().run(amain())
```

### Advanced Example

For more advanced usage, you can define multiple agents and manage their interactions. Here's an example of a self-developing agent that produces documentation:

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
async def echo_agent(ctx: InteractionContext, color: Union[str, int] = "92;1") -> None:
    ctx.reply(ctx.messages)
    async for msg_promise in ctx.messages:
        async for token in msg_promise:
            print(f"\033[{color};1m{token}\033[0m", end="", flush=True)
        print()
        print()

@miniagent
async def file_agent(ctx: InteractionContext, file: str) -> None:
    ctx.reply(ctx.messages)
    file = Path(file)
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("w", encoding="utf-8") as file_stream:
        async for readme_token in ctx.messages.as_single_promise():
            file_stream.write(readme_token)

@miniagent
async def readme_agent(_) -> None:
    experiment_name = input("\nEnter experiment folder name: ")
    experiment_name = "-".join(experiment_name.lower().split())
    if not experiment_name:
        experiment_name = "DEFAULT"
    for variation_idx, (variation_name, variation_skips) in enumerate(SKIPS_FOR_REPO_VARIATIONS.items()):
        for model_idx, (model, model_agent) in enumerate(MODEL_AGENTS.items()):
            md_file = SELF_DEV_OUTPUT / experiment_name / f"README-{variation_name}-{model}.md"
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

## Documentation

### Core Classes

- `MiniAgents`: The main context manager for managing agents and their interactions.
- `MiniAgent`: A wrapper for an agent function that allows calling the agent.
- `InteractionContext`: Provides context for an agent's interaction, including the messages and reply streamer.

### Message Handling

- `Message`: Represents a message that can be sent between agents.
- `MessagePromise`: A promise of a message that can be streamed token by token.
- `MessageSequencePromise`: A promise of a sequence of messages that can be streamed message by message.

### Promising

- `Promise`: Represents a promise of a value that will be resolved asynchronously.
- `StreamedPromise`: Represents a promise of a whole value that can be streamed piece by piece.
- `StreamAppender`: Allows appending pieces to a stream that is consumed by a `StreamedPromise`.

### Utilities

- `achain_loop`: Runs a loop of agents, chaining their interactions.
- `join_messages`: Joins multiple messages into a single message using a delimiter.
- `split_messages`: Splits messages based on a delimiter.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on the [GitHub repository](https://github.com/teremterem/MiniAgents).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the contributors and the open-source community for their support and contributions.
