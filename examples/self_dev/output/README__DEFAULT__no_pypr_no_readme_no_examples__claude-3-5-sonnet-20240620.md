# MiniAgents Framework

MiniAgents is a Python framework for building and managing asynchronous agent-based systems. It provides a flexible and extensible architecture for creating, chaining, and interacting with various types of agents, including those powered by large language models (LLMs).

## Key Features

- Asynchronous agent execution
- Flexible message passing between agents
- Support for streaming responses from LLMs
- Easy integration with OpenAI and Anthropic models
- Extensible architecture for custom agent types
- Promise-based asynchronous programming model
- Chat history management

## Installation

```bash
pip install miniagents
```

## Quick Start

Here's a simple example of how to use MiniAgents:

```python
from miniagents import MiniAgents, miniagent, InteractionContext
from miniagents.ext.llm.openai import openai_agent

@miniagent
async def user_agent(ctx: InteractionContext):
    ctx.reply("Hello, AI!")

@miniagent
async def main_agent(ctx: InteractionContext):
    user_message = await ctx.messages.aresolve_messages()
    ai_response = openai_agent.inquire(user_message, model="gpt-3.5-turbo")
    ctx.reply(ai_response)

async with MiniAgents():
    result = await main_agent.inquire(user_agent.inquire())
    print(await result.aresolve_messages())
```

## Core Concepts

### Agents

Agents are the basic building blocks of the MiniAgents framework. They are defined using the `@miniagent` decorator and can interact with each other through message passing.

### Messages

Messages are the primary means of communication between agents. They can contain text, metadata, and even nested messages.

### Promises

The framework uses a promise-based model for handling asynchronous operations. This allows for efficient handling of streaming responses and complex agent interactions.

### Contexts

MiniAgents uses context managers to handle the lifecycle of agents and promises, ensuring proper resource management and error handling.

## Advanced Features

### LLM Integration

MiniAgents provides built-in support for OpenAI and Anthropic language models, making it easy to create AI-powered agents.

### Chat History Management

The framework includes utilities for managing and persisting chat histories, including support for markdown-based storage.

### Extensibility

MiniAgents is designed to be easily extensible, allowing you to create custom agent types, message formats, and integrations with other services.

## Documentation

For more detailed information on how to use MiniAgents, please refer to the following sections:

- [API Reference](docs/api_reference.md)
- [Examples](docs/examples.md)
- [Advanced Usage](docs/advanced_usage.md)

## Contributing

Contributions to MiniAgents are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for more information on how to get started.

## License

MiniAgents is released under the [MIT License](LICENSE).

## Support

If you encounter any issues or have questions about using MiniAgents, please [open an issue](https://github.com/yourusername/miniagents/issues) on our GitHub repository.
