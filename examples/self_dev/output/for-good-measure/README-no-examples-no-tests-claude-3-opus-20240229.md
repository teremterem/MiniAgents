# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides a set of tools and abstractions for defining agents, managing their interactions, and integrating with large language models (LLMs) such as those from OpenAI and Anthropic.

## Key Features

- Define agents as Python functions decorated with `@miniagent`
- Agents can send and receive messages asynchronously
- Support for streaming messages piece-by-piece or token-by-token
- Integration with OpenAI and Anthropic LLMs out of the box
- Extensible architecture to add support for other LLMs
- Promise-based API for handling asynchronous operations
- Utilities for joining and splitting message sequences
- Context manager for managing the lifecycle of agents and promises

## Installation

You can install MiniAgents using pip:

```
pip install miniagents
```

## Usage

Here's a simple example of how to define an agent using MiniAgents:

```python
from miniagents import miniagent, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext, **kwargs):
    messages = await ctx.messages.aresolve_messages()
    response = f"You said: {messages[0].text}"
    ctx.reply(response)
```

To interact with the agent:

```python
from miniagents import MiniAgents

async with MiniAgents():
    result = await my_agent.inquire("Hello, agent!")
    print(result[0].text)  # Output: You said: Hello, agent!
```

For more detailed usage and examples, please refer to the documentation (TODO: Add link to documentation).

## Contributing

Contributions are welcome! If you find a bug, have a feature request, or want to contribute code, please open an issue or submit a pull request on the [GitHub repository](https://github.com/teremterem/MiniAgents).

## License

MiniAgents is released under the [MIT License](https://opensource.org/licenses/MIT).

## Things to remember (for the developer of this framework)

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders and what not should always catch
  BaseExceptions and not just Exceptions** when they capture errors to pass those errors as "pieces" in order for
  those errors to be raised at the "consumer side". This is because many of the aforementioned Promising "primitives"
  are often part of mechanisms that involve communications between async tasks via asyncio.Queue objects and just
  interrupting those promises with KeyboardInterrupt which are extended from BaseException instead of letting
  KeyboardInterrupt to go through the queue leads to hanging of those promises (a queue is waiting for END_OF_QUEUE
  sentinel forever but the task that should send it is dead).
