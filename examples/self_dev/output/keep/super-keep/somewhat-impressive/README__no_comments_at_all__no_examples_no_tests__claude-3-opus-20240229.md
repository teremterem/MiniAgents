# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides a simple and intuitive way to define agents and their interactions.

## Features

- Define agents as simple Python functions decorated with `@miniagent`
- Agents can send and receive messages asynchronously
- Agents can be chained together to form complex interaction flows
- Promises and async iterators are used extensively to enable non-blocking communication
- Extensible architecture allows integration with various LLM providers (OpenAI, Anthropic, etc.)
- Utilities for working with message sequences (joining, splitting, etc.)
- Frozen data structures for immutable agent state and message metadata
- Sentinels for special values (e.g. `NO_VALUE`, `DEFAULT`, `AWAIT`, etc.)

## Installation

```bash
pip install miniagents
```

## Usage

Here's a simple example of how to define an agent:

```python
from miniagents import miniagent, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext):
    async for message in ctx.messages:
        ctx.reply(f"You said: {message}")
```

And here's how to initiate an interaction with the agent:

```python
from miniagents import MiniAgents

async with MiniAgents():
    reply = await my_agent.inquire("Hello!")
    print(reply)  # prints "You said: Hello!"
```

For more advanced usage, check out the [examples](examples/) directory.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](LICENSE).

## Things to remember (for the developers of this framework)

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders and what not should always catch
  BaseExceptions and not just Exceptions** when they capture errors to pass those errors as "pieces" in order for
  those errors to be raised at the "consumer side". This is because many of the aforementioned Promising "primitives"
  are often part of mechanisms that involve communications between async tasks via asyncio.Queue objects and just
  interrupting those promises with KeyboardInterrupt which are extended from BaseException instead of letting
  KeyboardInterrupt to go through the queue leads to hanging of those promises (a queue is waiting for END_OF_QUEUE
  sentinel forever but the task that should send it is dead).
