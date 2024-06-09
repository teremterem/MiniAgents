# MiniAgents

MiniAgents is a Python framework designed to facilitate the creation and management of agents that interact with large language models (LLMs) and other asynchronous tasks. It provides a structured way to define, run, and manage agents, promises, and message sequences, making it easier to build complex, asynchronous workflows.

## Features

- **Agent Management**: Define and manage agents that can interact with LLMs or other asynchronous tasks.
- **Promise Handling**: Use promises to handle asynchronous operations and stream results piece by piece.
- **Message Sequences**: Manage sequences of messages, allowing for complex interactions and nested message handling.
- **LLM Integration**: Integrate with popular LLMs like OpenAI and Anthropic with built-in support.
- **Error Handling**: Robust error handling mechanisms to ensure smooth operation even in the presence of exceptions.

## Installation

To install MiniAgents, you can use `poetry`:

```sh
poetry add miniagents
```

## Usage

### Defining Agents

You can define agents using the `@miniagent` decorator. Agents are asynchronous functions that interact with messages and other agents.

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext) -> None:
    ctx.reply("Hello, world!")
```

### Running Agents

To run agents, you need to create a `MiniAgents` context and use the `inquire` method to send messages to the agent.

```python
from miniagents.miniagents import MiniAgents

async def main():
    async with MiniAgents():
        response = await my_agent.inquire("Hello!")
        print(await response.aresolve_messages())

import asyncio
asyncio.run(main())
```

### Integrating with LLMs

MiniAgents provides built-in support for integrating with LLMs like OpenAI and Anthropic.

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent(model="gpt-3.5-turbo")

async def main():
    async with MiniAgents():
        response = await openai_agent.inquire("Tell me a joke.")
        print(await response.aresolve_messages())

import asyncio
asyncio.run(main())
```

### Handling Promises

MiniAgents uses promises to handle asynchronous operations. You can create promises for messages and message sequences.

```python
from miniagents.messages import Message

message_promise = Message.promise(text="This is a promise.")
```

### Error Handling

MiniAgents provides robust error handling mechanisms to ensure smooth operation even in the presence of exceptions.

```python
from miniagents.promising.errors import PromisingError

try:
    # Your code here
except PromisingError as e:
    print(f"An error occurred: {e}")
```

## Things to Remember (for the developer of this framework)

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders, and what not should always catch `BaseExceptions` and not just `Exceptions`** when they capture errors to pass those errors as "pieces" in order for those errors to be raised at the "consumer side". This is because many of the aforementioned Promising "primitives" are often part of mechanisms that involve communications between async tasks via `asyncio.Queue` objects and just interrupting those promises with `KeyboardInterrupt` which are extended from `BaseException` instead of letting `KeyboardInterrupt` to go through the queue leads to hanging of those promises (a queue is waiting for `END_OF_QUEUE` sentinel forever but the task that should send it is dead).

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on GitHub.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Authors

- Oleksandr Tereshchenko - [toporok@gmail.com](mailto:toporok@gmail.com)

## Acknowledgments

- Special thanks to the developers of the libraries and tools that made this project possible.

For more details, visit the [GitHub repository](https://github.com/teremterem/MiniAgents).
