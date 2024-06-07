# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of agents that interact with each other through messages. It provides a robust and flexible system for handling asynchronous tasks, promises, and message sequences, making it ideal for building complex, interactive applications.

## Features

- **Agent Management**: Easily create and manage agents that can interact with each other.
- **Asynchronous Promises**: Handle asynchronous tasks and promises with ease.
- **Message Sequences**: Manage sequences of messages, including nested and streamed messages.
- **Integration with LLMs**: Integrate with language models like OpenAI and Anthropic.
- **Error Handling**: Robust error handling mechanisms to ensure smooth operation.

## Installation

To install MiniAgents, you can use `poetry`:

```bash
poetry install
```

## Usage

### Creating an Agent

You can create an agent using the `@miniagent` decorator. Here's a simple example:

```python
from miniagents.miniagents import miniagent, MiniAgents

@miniagent
async def my_agent(ctx):
    ctx.reply("Hello, World!")

async with MiniAgents():
    response = await my_agent.inquire()
    print(await response.aresolve_messages())
```

### Integrating with Language Models

MiniAgents provides integration with language models like OpenAI and Anthropic. Here's how you can create agents for these models:

#### OpenAI

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent(model="gpt-3.5-turbo")

async with MiniAgents():
    response = await openai_agent.inquire("Hello, OpenAI!")
    print(await response.aresolve_messages())
```

#### Anthropic

```python
from miniagents.ext.llm.anthropic import create_anthropic_agent

anthropic_agent = create_anthropic_agent(model="claude-3")

async with MiniAgents():
    response = await anthropic_agent.inquire("Hello, Anthropic!")
    print(await response.aresolve_messages())
```

### Handling Message Sequences

MiniAgents allows you to manage sequences of messages, including nested and streamed messages. Here's an example:

```python
from miniagents.messages import MessageSequence

async with MiniAgents():
    msg_seq = MessageSequence()
    with msg_seq.message_appender:
        msg_seq.message_appender.append("Message 1")
        msg_seq.message_appender.append("Message 2")

    messages = await msg_seq.sequence_promise.aresolve_messages()
    for msg in messages:
        print(msg.text)
```

## Error Handling

MiniAgents provides robust error handling mechanisms. You can define custom error handlers for promises and message sequences.

```python
from miniagents.promising.errors import PromisingError

async def custom_error_handler(promise, error):
    print(f"Error in promise: {error}")

async with MiniAgents(on_promise_resolved=custom_error_handler):
    # Your code here
```

## Testing

MiniAgents includes a comprehensive test suite. To run the tests, use `pytest`:

```bash
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on GitHub.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Developer Notes

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders and what not should always catch BaseExceptions and not just Exceptions** when they capture errors to pass those errors as "pieces" in order for those errors to be raised at the "consumer side". This is because many of the aforementioned Promising "primitives" are often part of mechanisms that involve communications between async tasks via `asyncio.Queue` objects and just interrupting those promises with `KeyboardInterrupt` which are extended from `BaseException` instead of letting `KeyboardInterrupt` to go through the queue leads to hanging of those promises (a queue is waiting for `END_OF_QUEUE` sentinel forever but the task that should send it is dead).

## Acknowledgements

Special thanks to Oleksandr Tereshchenko for developing and maintaining this framework.
