# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of agents that interact with large language models (LLMs) and other asynchronous tasks. The framework provides a structured way to define, run, and manage these agents, making it easier to build complex, interactive applications.

## Features

- **Agent Management**: Define and manage agents that can interact with each other and external services.
- **LLM Integration**: Seamlessly integrate with popular LLMs like OpenAI and Anthropic.
- **Message Handling**: Stream and process messages between agents efficiently.
- **Promise-Based Architecture**: Use promises to handle asynchronous tasks and streams.
- **Extensibility**: Easily extend the framework to support new types of agents and interactions.

## Installation

To install MiniAgents, you can use [Poetry](https://python-poetry.org/):

```sh
poetry add miniagents
```

## Usage

### Basic Example

Here's a basic example of how to use MiniAgents to create a simple conversation loop with an OpenAI agent:

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

For more advanced usage, including integrating with multiple LLMs and handling complex interactions, refer to the examples in the `examples` directory.

## Extending MiniAgents

MiniAgents is designed to be extensible. You can create your own agents and integrate them with the framework. Here's an example of how to create a custom agent:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def custom_agent(ctx: InteractionContext) -> None:
    async for msg_promise in ctx.messages:
        async for token in msg_promise:
            print(f"Custom Agent received: {token}")
        ctx.reply("Response from Custom Agent")

# Use the custom agent in your application
```

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Developer Notes

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders and what not should always catch BaseExceptions and not just Exceptions** when they capture errors to pass those errors as "pieces" in order for those errors to be raised at the "consumer side". This is because many of the aforementioned Promising "primitives" are often part of mechanisms that involve communications between async tasks via asyncio.Queue objects and just interrupting those promises with KeyboardInterrupt which are extended from BaseException instead of letting KeyboardInterrupt to go through the queue leads to hanging of those promises (a queue is waiting for END_OF_QUEUE sentinel forever but the task that should send it is dead).

## Acknowledgements

Special thanks to the developers and contributors of the libraries and tools that made this project possible.

---

For more information, visit the [MiniAgents GitHub repository](https://github.com/teremterem/MiniAgents).
