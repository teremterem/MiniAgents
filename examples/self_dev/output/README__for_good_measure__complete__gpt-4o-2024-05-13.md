# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of agents that interact with large language models (LLMs) and other asynchronous tasks. The framework provides a structured way to define agents, manage their interactions, and handle asynchronous communication between them.

## Features

- **Agent Definition**: Easily define agents using the `@miniagent` decorator.
- **Asynchronous Communication**: Manage asynchronous interactions between agents using promises and streams.
- **LLM Integration**: Integrate with popular LLMs like OpenAI and Anthropic.
- **Message Handling**: Stream and handle messages token by token.
- **Error Handling**: Robust error handling mechanisms to ensure smooth operation.

## Installation

To install MiniAgents, you can use `poetry`:

```bash
poetry install
```

## Usage

### Basic Example

Here's a basic example of how to define and run agents using MiniAgents:

```python
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext

@miniagent
async def example_agent(ctx: InteractionContext) -> None:
    async for msg_promise in ctx.messages:
        async for token in msg_promise:
            print(token, end="", flush=True)
        print()

async def amain() -> None:
    await example_agent.inquire("Hello, MiniAgents!").aresolve_messages()

if __name__ == "__main__":
    MiniAgents().run(amain())
```

### LLM Integration

You can integrate with LLMs like OpenAI and Anthropic. Here's an example using OpenAI:

```python
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.miniagents import MiniAgents

llm_agent = create_openai_agent(model="gpt-4")

async def amain() -> None:
    reply_sequence = llm_agent.inquire("How are you today?", max_tokens=100)
    async for msg_promise in reply_sequence:
        async for token in msg_promise:
            print(token, end="", flush=True)
        print()

if __name__ == "__main__":
    MiniAgents().run(amain())
```

### Advanced Example

For more advanced usage, you can define multiple agents and manage their interactions:

```python
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext
from miniagents.promising.sentinels import AWAIT
from miniagents.utils import achain_loop

@miniagent
async def user_agent(ctx: InteractionContext) -> None:
    async for msg_promise in ctx.messages:
        async for token in msg_promise:
            print(token, end="", flush=True)
        print()
    ctx.reply(input("USER: "))

@miniagent
async def assistant_agent(ctx: InteractionContext) -> None:
    async for msg_promise in ctx.messages:
        async for token in msg_promise:
            print(token, end="", flush=True)
        print()
    ctx.reply("Hello, how can I assist you?")

async def amain() -> None:
    await achain_loop([user_agent, AWAIT, assistant_agent])

if __name__ == "__main__":
    MiniAgents().run(amain())
```

## Testing

To run tests, you can use `pytest`:

```bash
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on GitHub.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Developer Notes

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders and what not should always catch `BaseExceptions` and not just `Exceptions`** when they capture errors to pass those errors as "pieces" in order for those errors to be raised at the "consumer side". This is because many of the aforementioned Promising "primitives" are often part of mechanisms that involve communications between async tasks via `asyncio.Queue` objects and just interrupting those promises with `KeyboardInterrupt` which are extended from `BaseException` instead of letting `KeyboardInterrupt` to go through the queue leads to hanging of those promises (a queue is waiting for `END_OF_QUEUE` sentinel forever but the task that should send it is dead).

## Contact

For any questions or suggestions, please contact Oleksandr Tereshchenko at [toporok@gmail.com](mailto:toporok@gmail.com).
