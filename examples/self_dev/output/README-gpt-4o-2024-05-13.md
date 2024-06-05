# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of asynchronous agents that can interact with each other through messages. It provides a robust and flexible architecture for building complex systems involving multiple agents, such as chatbots, automated assistants, and more.

## Features

- **Asynchronous Agents**: Easily create and manage agents that operate asynchronously.
- **Message Passing**: Agents communicate through a powerful message-passing system.
- **Integration with LLMs**: Built-in support for integrating with large language models (LLMs) like OpenAI and Anthropic.
- **Promise-based Architecture**: Utilizes a promise-based architecture for handling asynchronous operations and streaming data.
- **Extensible**: Easily extend the framework to add new functionalities or integrate with other systems.

## Installation

To install MiniAgents, you can use `poetry`:

```bash
poetry add miniagents
```

## Quick Start

Here's a simple example to get you started with MiniAgents:

```python
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext
from miniagents.promising.sentinels import AWAIT
from miniagents.utils import achain_loop

@miniagent
async def user_agent(ctx: InteractionContext) -> None:
    print("\033[92;1m", end="", flush=True)
    async for msg_promise in ctx.messages:
        print(f"\n{msg_promise.preliminary_metadata.agent_alias}: ", end="", flush=True)
        async for token in msg_promise:
            print(token, end="", flush=True)
        print("\n")

    ctx.reply(input("USER: "))

async def amain() -> None:
    try:
        print()
        await achain_loop(
            [
                user_agent,
                AWAIT,
            ]
        )
    except KeyboardInterrupt:
        ...
    finally:
        print("\033[0m\n")

if __name__ == "__main__":
    MiniAgents().run(amain())
```

## Examples

### Using LLMs

You can integrate with LLMs like OpenAI and Anthropic. Here's an example of using OpenAI's GPT model:

```python
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

### Self-Development Agents

MiniAgents can also be used for self-development tasks, such as generating documentation:

```python
from examples.self_dev.self_dev_common import FullRepoMessage, MODEL_AGENTS, SELF_DEV_OUTPUT
from examples.self_dev.self_dev_prompts import GLOBAL_SYSTEM_HEADER, PRODUCE_README_SYSTEM_FOOTER
from miniagents.ext.llm.llm_common import SystemMessage
from miniagents.miniagents import miniagent, MiniAgents, InteractionContext

@miniagent
async def readme_agent(_) -> None:
    inpt = [
        SystemMessage(GLOBAL_SYSTEM_HEADER),
        FullRepoMessage(),
        SystemMessage(PRODUCE_README_SYSTEM_FOOTER),
    ]

    for idx, (model, model_agent) in enumerate(MODEL_AGENTS.items()):
        echo_agent.inquire(
            file_agent.inquire(
                model_agent.inquire(
                    inpt,
                    temperature=0,
                ),
                file=str(SELF_DEV_OUTPUT / f"README-{model}.md"),
            ),
            color=f"{92 + idx};1",
        )

async def amain() -> None:
    async with MiniAgents():
        readme_agent.inquire()
    print("Readme file(s) produced")

if __name__ == "__main__":
    asyncio.run(amain())
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on GitHub.

## Acknowledgements

Special thanks to the developers and contributors of the libraries and tools that made this project possible.

## Contact

For any inquiries or questions, please contact Oleksandr Tereshchenko at [toporok@gmail.com](mailto:toporok@gmail.com).
