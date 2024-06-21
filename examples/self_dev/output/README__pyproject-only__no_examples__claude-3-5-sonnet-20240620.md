# MiniAgents

MiniAgents is an asynchronous framework for building LLM-based multi-agent systems in Python, with a focus on immutable messages and token streaming.

## Features

- Asynchronous design for efficient handling of concurrent operations
- Support for immutable messages to ensure data integrity
- Token streaming capabilities for real-time processing
- Integration with popular LLM providers (OpenAI, Anthropic)
- Extensible architecture for custom agent implementations

## Installation

```bash
pip install miniagents
```

## Quick Start

Here's a simple example of how to use MiniAgents:

```python
from miniagents import MiniAgents, miniagent, InteractionContext
from miniagents.ext.llm.openai import create_openai_agent

@miniagent
async def user_agent(ctx: InteractionContext):
    ctx.reply("Hello, AI assistant!")

ai_agent = create_openai_agent(model="gpt-3.5-turbo")

async with MiniAgents():
    user_message = user_agent.inquire()
    ai_response = ai_agent.inquire(user_message)

    async for message in ai_response:
        print(await message)
```

## Key Components

- `MiniAgents`: The main context manager for running agent interactions
- `miniagent`: A decorator for creating custom agents
- `InteractionContext`: Provides context for agent interactions
- `Message`: Represents immutable messages exchanged between agents
- `MessagePromise`: A promise for asynchronous message delivery
- `StreamedPromise`: Allows for token-by-token streaming of messages

## Extensions

MiniAgents includes extensions for popular LLM providers:

- OpenAI (`miniagents.ext.llm.openai`)
- Anthropic (`miniagents.ext.llm.anthropic`)

## Advanced Usage

The framework supports complex agent interactions, message chaining, and custom LLM integrations. Refer to the documentation for more advanced usage scenarios.

## Contributing

Contributions are welcome! Please check out the [contribution guidelines](CONTRIBUTING.md) for more information.

## License

MiniAgents is released under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

For questions, issues, or feature requests, please open an issue on the [GitHub repository](https://github.com/teremterem/MiniAgents).
