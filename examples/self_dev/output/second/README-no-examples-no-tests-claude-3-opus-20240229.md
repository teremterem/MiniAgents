# MiniAgents

MiniAgents is a Python framework for building and interacting with AI agents. It provides a set of tools and abstractions to facilitate the development of agent-based systems.

## Key Features

- **Agent Definition**: Define agents using the `@miniagent` decorator, which converts an agent function into a `MiniAgent` object.
- **Message Handling**: Handle messages between agents using the `Message` and `MessagePromise` classes, which support streaming and asynchronous processing.
- **Interaction Context**: Use the `InteractionContext` class to manage the context of agent interactions, including input messages and reply handling.
- **Promise-based Asynchronous Programming**: Utilize the `Promise`, `StreamedPromise`, and related classes for asynchronous programming and handling of promises.
- **Sequence Handling**: Work with sequences of messages using the `MessageSequence` and `FlatSequence` classes.
- **Utility Functions**: Leverage utility functions like `join_messages`, `split_messages`, and `achain_loop` for common tasks.
- **Integration with Language Models**: Integrate with language models from Anthropic and OpenAI using the `anthropic.py` and `openai.py` modules.

## Installation

You can install MiniAgents using Poetry:

```bash
poetry add miniagents
```

## Usage

Here's a basic example of how to define and interact with agents using MiniAgents:

```python
from miniagents import miniagent, InteractionContext, MessageType

@miniagent
async def my_agent(ctx: InteractionContext, **kwargs) -> None:
    input_messages = await ctx.messages.aresolve_messages()
    # Process input messages and generate a response
    response = f"Hello, you said: {input_messages[0].text}"
    ctx.reply(response)

# Create an instance of the agent
agent = my_agent()

# Send a message to the agent and get the response
response = agent.inquire("Hi there!")
print(response.text)  # Output: Hello, you said: Hi there!
```

For more detailed usage examples and documentation, please refer to the [MiniAgents documentation](https://github.com/teremterem/MiniAgents).

## Contributing

Contributions to MiniAgents are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request on the [GitHub repository](https://github.com/teremterem/MiniAgents).

## License

MiniAgents is released under the [MIT License](https://github.com/teremterem/MiniAgents/blob/main/LICENSE).

## Things to remember (for the developer of this framework)

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders and what not should always catch
  BaseExceptions and not just Exceptions** when they capture errors to pass those errors as "pieces" in order for
  those errors to be raised at the "consumer side". This is because many of the aforementioned Promising "primitives"
  are often part of mechanisms that involve communications between async tasks via asyncio.Queue objects and just
  interrupting those promises with KeyboardInterrupt which are extended from BaseException instead of letting
  KeyboardInterrupt to go through the queue leads to hanging of those promises (a queue is waiting for END_OF_QUEUE
  sentinel forever but the task that should send it is dead).
