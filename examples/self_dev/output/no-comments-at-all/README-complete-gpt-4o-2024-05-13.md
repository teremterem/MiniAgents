# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of asynchronous agents. These agents can interact with each other, process messages, and perform various tasks in parallel. The framework is built with extensibility in mind, allowing for easy integration with different large language models (LLMs) and other external services.

## Features

- **Asynchronous Agents**: Create and manage agents that can run tasks concurrently.
- **Message Handling**: Define and process messages between agents.
- **Extensible**: Easily integrate with different LLMs like OpenAI and Anthropic.
- **Promise-based**: Utilize promises for handling asynchronous operations and message sequences.
- **Utilities**: Various utility functions to aid in agent interactions and message processing.

## Installation

To install MiniAgents, you can use `poetry`:

```sh
poetry install
```

## Usage

### Basic Example

Here's a basic example of how to create and run a simple agent using MiniAgents:

```python
import asyncio
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext

@miniagent
async def simple_agent(ctx: InteractionContext) -> None:
    print("Agent is running")
    ctx.reply("Hello from the agent!")

async def main() -> None:
    async with MiniAgents():
        await simple_agent.inquire()

if __name__ == "__main__":
    asyncio.run(main())
```

### Integrating with OpenAI

You can create an agent that interacts with OpenAI's GPT models:

```python
from dotenv import load_dotenv
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.miniagents import MiniAgents

load_dotenv()

llm_agent = create_openai_agent(model="gpt-4o-2024-05-13")

async def main() -> None:
    async with MiniAgents():
        reply_sequence = llm_agent.inquire("How are you today?", max_tokens=1000, temperature=0.0)
        async for msg_promise in reply_sequence:
            async for token in msg_promise:
                print(token, end="", flush=True)
            print()

if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced Example with Multiple Agents

You can create more complex interactions involving multiple agents:

```python
import asyncio
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext

@miniagent
async def agent1(ctx: InteractionContext) -> None:
    print("Agent 1 is running")
    ctx.reply("Message from Agent 1")

@miniagent
async def agent2(ctx: InteractionContext) -> None:
    print("Agent 2 is running")
    ctx.reply("Message from Agent 2")

@miniagent
async def aggregator_agent(ctx: InteractionContext) -> None:
    ctx.reply([agent1.inquire(), agent2.inquire()])

async def main() -> None:
    async with MiniAgents():
        await aggregator_agent.inquire()

if __name__ == "__main__":
    asyncio.run(main())
```

## Testing

MiniAgents includes a suite of tests to ensure the framework works as expected. To run the tests, you can use `pytest`:

```sh
pytest
```

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request on the [GitHub repository](https://github.com/teremterem/MiniAgents).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the developers and contributors of the libraries and tools that made this project possible, including `pydantic`, `openai`, `anthropic`, and others.

---

This README provides an overview of the MiniAgents framework, its features, installation instructions, usage examples, and information on testing and contributing. For more detailed documentation, please refer to the source code and comments within the project.
