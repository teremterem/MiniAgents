# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of agents that interact with large language models (LLMs) and other asynchronous tasks. The framework provides a robust and flexible way to build, chain, and manage agents, making it easier to develop complex conversational and interactive applications.

## Features

- **Agent Management**: Easily create and manage agents using decorators and context managers.
- **LLM Integration**: Seamlessly integrate with popular LLMs like OpenAI and Anthropic.
- **Message Handling**: Stream and handle messages between agents with support for token-level streaming.
- **Promise-Based Architecture**: Utilize promises for asynchronous operations, ensuring smooth and efficient task management.
- **Extensibility**: Extend the framework with custom agents, message types, and more.

## Installation

To install MiniAgents, you can use `poetry`:

```sh
poetry add miniagents
```

## Usage

### Basic Example

Here's a basic example of how to use MiniAgents to create a simple conversation loop with an OpenAI agent:

```python
import asyncio
from dotenv import load_dotenv
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext
from miniagents.promising.sentinels import AWAIT
from miniagents.utils import achain_loop

load_dotenv()

CHAT_HISTORY = []

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

For more advanced usage, including handling multiple agents and custom message types, refer to the examples provided in the `examples` directory.

## Examples

### Conversation Example

The `examples/conversation.py` file demonstrates how to set up a simple conversation loop with an OpenAI agent.

### LLM Example

The `examples/llm_example.py` file shows how to interact with an LLM and print the response.

### Self-Development Example

The `examples/self_dev` directory contains examples of agents that specialize in producing documentation for the MiniAgents framework.

## Extending MiniAgents

MiniAgents is designed to be extensible. You can create custom agents, message types, and more by following the patterns established in the framework.

### Creating a Custom Agent

To create a custom agent, use the `@miniagent` decorator:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def custom_agent(ctx: InteractionContext) -> None:
    # Your custom agent logic here
    ctx.reply("Hello from custom agent!")
```

### Integrating with Other LLMs

You can integrate with other LLMs by creating agents using the provided integration modules, such as `miniagents.ext.llm.openai` and `miniagents.ext.llm.anthropic`.

## Contributing

Contributions are welcome! Please refer to the [CONTRIBUTING.md](https://github.com/teremterem/MiniAgents/blob/main/CONTRIBUTING.md) file for guidelines on how to contribute to the project.

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/teremterem/MiniAgents/blob/main/LICENSE) file for details.

## Contact

For any questions or inquiries, please contact Oleksandr Tereshchenko at [toporok@gmail.com](mailto:toporok@gmail.com).
