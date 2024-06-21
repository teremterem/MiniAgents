# MiniAgents

MiniAgents is an asynchronous framework for building LLM-based multi-agent systems in Python, with a focus on immutable messages and token streaming.

## Features

- Asynchronous design for efficient handling of multiple agents
- Immutable message handling for reliable communication between agents
- Token streaming support for real-time processing of LLM outputs
- Extensible architecture for easy integration with various LLM providers
- Built-in support for OpenAI and Anthropic models
- Flexible agent creation and chaining capabilities

## Installation

You can install MiniAgents using pip:

```bash
pip install miniagents
```

## Quick Start

Here's a simple example of how to use MiniAgents:

```python
import asyncio
from miniagents.miniagents import miniagent, MiniAgents
from miniagents.ext.llm.openai import create_openai_agent

async def main():
    async with MiniAgents():
        openai_agent = create_openai_agent(model="gpt-3.5-turbo")

        @miniagent
        async def echo_agent(ctx):
            async for message in ctx.messages:
                ctx.reply(f"Echo: {message}")

        result = await openai_agent.inquire("Tell me a joke")
        await echo_agent.inquire(result)

asyncio.run(main())
```

## Key Components

- `MiniAgents`: The main context manager for managing agent interactions
- `miniagent`: A decorator for creating custom agents
- `InteractionContext`: Provides context for agent interactions
- `MessagePromise` and `MessageSequencePromise`: For handling asynchronous message streams
- `ChatHistory`: For managing and persisting chat histories

## Extensions

MiniAgents includes extensions for:

- OpenAI and Anthropic LLM integration
- Console-based user interaction
- Markdown-based chat history storage

## Advanced Usage

For more advanced usage, including chaining multiple agents, custom LLM integrations, and working with chat histories, please refer to the documentation and examples in the repository.

## Contributing

Contributions to MiniAgents are welcome! Please refer to the contributing guidelines in the repository for more information.

## License

MiniAgents is released under the MIT License. See the LICENSE file for more details.

## Contact

For questions and support, please open an issue on the GitHub repository.
