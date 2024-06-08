# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of agents that interact with language models (LLMs) such as OpenAI and Anthropic. The framework provides a structured way to define, call, and manage agents, making it easier to build complex interactions with LLMs.

## Features

- **Agent Management**: Define and manage agents with ease.
- **LLM Integration**: Seamlessly integrate with OpenAI and Anthropic language models.
- **Message Handling**: Stream and handle messages between agents.
- **Promise-Based Architecture**: Use promises to manage asynchronous operations and message streaming.
- **Utilities**: Various utility functions to handle message sequences, joining, splitting, and more.

## Installation

To install MiniAgents, you can use [Poetry](https://python-poetry.org/):

```sh
poetry add miniagents
```

## Usage

### Creating an Agent

You can create an agent using the `miniagent` decorator. Here's an example of how to create a simple agent:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext, **kwargs):
    ctx.reply("Hello, I am your agent!")
```

### Integrating with OpenAI

To create an agent that interacts with OpenAI's language model, you can use the `create_openai_agent` function:

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent()
```

### Integrating with Anthropic

Similarly, to create an agent that interacts with Anthropic's language model, use the `create_anthropic_agent` function:

```python
from miniagents.ext.llm.anthropic import create_anthropic_agent

anthropic_agent = create_anthropic_agent()
```

### Running an Agent

To run an agent and get its response, you can use the `inquire` method:

```python
response = await openai_agent.inquire("What is the capital of France?")
print(response)
```

### Using Promises

MiniAgents uses a promise-based architecture to handle asynchronous operations. You can create and manage promises for messages:

```python
from miniagents.messages import Message

message_promise = Message.promise(text="Hello, world!")
resolved_message = await message_promise
print(resolved_message)
```

### Utilities

MiniAgents provides various utility functions to handle message sequences, joining, splitting, and more:

```python
from miniagents.utils import join_messages, split_messages

# Join messages
joined_message = join_messages(["Hello", "world"], delimiter=" ")
print(await joined_message)

# Split messages
split_message_sequence = split_messages("Hello\n\nworld")
for message in await split_message_sequence:
    print(message)
```

## Configuration

You can configure MiniAgents using the `MiniAgents` class. For example, to set the default behavior for streaming LLM tokens:

```python
from miniagents.miniagents import MiniAgents

mini_agents = MiniAgents(stream_llm_tokens_by_default=True)
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on the [GitHub repository](https://github.com/teremterem/MiniAgents).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Authors

- Oleksandr Tereshchenko - [toporok@gmail.com](mailto:toporok@gmail.com)

## Acknowledgments

Special thanks to the developers and contributors of the libraries and tools that made this project possible.

---

For more detailed documentation and examples, please refer to the [official documentation](https://github.com/teremterem/MiniAgents).
