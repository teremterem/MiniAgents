Here's a clean and informative README.md for the MiniAgents framework:

# MiniAgents

MiniAgents is a Python framework for building flexible and extensible agent-based systems, with a focus on language model interactions and asynchronous communication. It provides a simple yet powerful way to define, manage, and chain multiple agents, enabling complex interactions and workflows.

## Features

- **Agent Management**: Easily create, manage, and chain multiple agents using simple decorators.
- **Asynchronous Execution**: Built on asyncio for efficient parallel processing and non-blocking operations.
- **LLM Integration**: Seamless integration with popular language models like OpenAI's GPT and Anthropic's Claude.
- **Message Handling**: Robust message passing system with support for nested messages and promises.
- **Chat History**: Flexible chat history management, including in-memory and Markdown-based persistence.
- **Streaming**: Support for token-by-token and message-by-message streaming.
- **Immutable Messages**: Ensures reproducibility and predictability in agent interactions.
- **Extensible Architecture**: Easily integrate with various LLM providers and extend functionality.

## Installation

```bash
pip install miniagents
```

## Quick Start

Here's a simple example of how to define and use an agent:

```python
from miniagents import miniagent, MiniAgents, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext):
    async for message in ctx.messages:
        ctx.reply(f"You said: {message}")

async def main():
    async with MiniAgents():
        reply = await my_agent.inquire("Hello, MiniAgents!")
        print(await reply.aresolve_messages())

MiniAgents().run(main())
```

## Key Concepts

- **MiniAgent**: A wrapper for agent functions, allowing easy definition and interaction.
- **InteractionContext**: Provides context for agent interactions, including messages and reply methods.
- **Message**: Represents messages passed between agents, with support for metadata and nested structures.
- **Promise**: Represents asynchronous operations, allowing for non-blocking execution.

## Advanced Usage

### LLM Integration

```python
from miniagents.ext.llm.openai import openai_agent

async def main():
    async with MiniAgents():
        llm_agent = openai_agent.fork(model="gpt-3.5-turbo")
        reply = await llm_agent.inquire("Tell me a joke")
        print(await reply.aresolve_messages())

MiniAgents().run(main())
```

### Chaining Agents

```python
from miniagents.utils import achain_loop

async def main():
    async with MiniAgents():
        await achain_loop([user_agent, AWAIT, assistant_agent])

MiniAgents().run(main())
```

## Documentation

For more detailed documentation, please refer to the docstrings in the source code and the examples provided in the `examples/` directory.

## Contributing

Contributions are welcome! Please see the `CONTRIBUTING.md` file for guidelines.

## License

MiniAgents is released under the MIT License. See the `LICENSE` file for details.

## Acknowledgements

MiniAgents is built on top of the Promising library for managing asynchronous operations.

---

This README provides an overview of the MiniAgents framework, its key features, installation instructions, and basic usage examples. It also points users to more detailed documentation and contribution guidelines. You may want to expand on certain sections or add more examples based on the specific use cases and complexities of your framework.
