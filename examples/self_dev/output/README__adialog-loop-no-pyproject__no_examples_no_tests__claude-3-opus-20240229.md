# MiniAgents

MiniAgents is a Python framework for building multi-agent systems with a focus on natural language processing and large language models.

## Features

- Abstractions for defining agents and their interactions
- Support for streaming messages and tokens for efficient communication
- Integration with Anthropic and OpenAI language models
- Utilities for working with chat history and markdown files
- Promise-based asynchronous programming model for handling complex agent interactions

## Installation

```bash
pip install miniagents
```

## Usage

### Defining Agents

To define an agent, use the `@miniagent` decorator on an async function:

```python
from miniagents import miniagent, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext):
    # Agent logic goes here
    ctx.reply("Hello, I'm an agent!")
```

### Interacting with Agents

To interact with an agent, use the `inquire` method:

```python
response = await my_agent.inquire("What's your name?")
print(response)  # Output: Hello, I'm an agent!
```

### Integrating with Language Models

MiniAgents provides integration with Anthropic and OpenAI language models. Here's an example of using an OpenAI model:

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent(model="gpt-3.5-turbo")
response = await openai_agent.inquire("What is the capital of France?")
print(response)  # Output: The capital of France is Paris.
```

### Working with Chat History

MiniAgents includes utilities for working with chat history, such as loading and saving chat history to markdown files:

```python
from miniagents.ext.chat_history_md import ChatHistoryMD

chat_history = ChatHistoryMD("chat_history.md")
await chat_history.aload_chat_history()
# ...
await chat_history.logging_agent.inquire(response)
```

## Documentation

For more detailed documentation and examples, please refer to the [MiniAgents documentation](https://miniagents.readthedocs.io/).

## Contributing

Contributions are welcome! Please see the [contributing guidelines](CONTRIBUTING.md) for more information.

## License

MiniAgents is released under the [MIT License](LICENSE).
