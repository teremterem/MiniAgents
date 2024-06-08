# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of mini agents that can interact with each other and external systems. The framework provides a structured way to define agents, manage their interactions, and handle asynchronous communication.

## Features

- **Agent Definition**: Easily define agents using decorators.
- **Asynchronous Communication**: Handle asynchronous interactions between agents.
- **LLM Integration**: Integrate with large language models (LLMs) like OpenAI and Anthropic.
- **Message Handling**: Stream and manage messages between agents.
- **Persistence**: Persist messages for later use or analysis.

## Installation

To install MiniAgents, you can use `poetry`:

```bash
poetry install
```

## Usage

### Defining Agents

You can define an agent using the `@miniagent` decorator. Here is an example of a simple user agent:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def user_agent(ctx: InteractionContext) -> None:
    print("User agent activated")
    ctx.reply("Hello from user agent")
```

### Running Agents

To run agents, you can use the `MiniAgents` context manager and the `run` method:

```python
from miniagents.miniagents import MiniAgents

async def amain() -> None:
    await user_agent.inquire()

if __name__ == "__main__":
    MiniAgents().run(amain())
```

### Integrating with LLMs

MiniAgents provides integration with LLMs like OpenAI and Anthropic. You can create an LLM agent and use it in your interactions:

```python
from miniagents.ext.llm.openai import create_openai_agent

llm_agent = create_openai_agent(model="gpt-4")

async def amain() -> None:
    response = await llm_agent.inquire("How are you?")
    print(response)

if __name__ == "__main__":
    MiniAgents().run(amain())
```

### Examples

#### Conversation Example

This example demonstrates a simple conversation between a user and an LLM agent:

```python
import readline
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
                create_openai_agent(model="gpt-4"),
            ]
        )
    except KeyboardInterrupt:
        ...
    finally:
        print("\033[0m\n")

if __name__ == "__main__":
    MiniAgents().run(amain())
```

#### LLM Example

This example shows how to use an LLM agent to get a response in Yoda-speak:

```python
from pprint import pprint
from dotenv import load_dotenv
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.messages import Message
from miniagents.miniagents import MiniAgents

load_dotenv()

llm_agent = create_openai_agent(model="gpt-4")

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

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on GitHub.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the developers and contributors of the libraries and tools used in this project.

## Contact

For any questions or inquiries, please contact Oleksandr Tereshchenko at [toporok@gmail.com](mailto:toporok@gmail.com).
