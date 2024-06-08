# MiniAgents

MiniAgents is a Python framework for building multi-agent systems with a focus on conversational AI agents powered by large language models (LLMs).

## Features

- Asynchronous and parallel execution of agents
- Streaming of messages and tokens for efficient memory usage
- Integration with OpenAI and Anthropic LLMs
- Flexible message passing between agents
- Immutable message and agent state for reproducibility
- Promises and async iterators for managing asynchronous operations
- Utilities for working with message sequences

## Installation

```bash
pip install miniagents
```

## Usage

Here's a basic example of creating and running agents:

```python
from miniagents import MiniAgents, miniagent, InteractionContext

@miniagent
async def hello_agent(ctx: InteractionContext):
    ctx.reply("Hello!")

@miniagent
async def world_agent(ctx: InteractionContext):
    ctx.reply("World!")

async def main():
    async with MiniAgents():
        hello = hello_agent.inquire()
        world = world_agent.inquire()
        print(await hello.aresolve_messages())
        print(await world.aresolve_messages())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

This will print:
```
(Message(text='Hello!'),)
(Message(text='World!'),)
```

See the `examples/` directory for more usage examples.

## Documentation

Full API documentation is available at https://miniagents.readthedocs.io/

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is open-source under the [MIT License](LICENSE).

## Things to remember (for the developer of this framework)

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders and what not should always catch
  BaseExceptions and not just Exceptions** when they capture errors to pass those errors as "pieces" in order for
  those errors to be raised at the "consumer side". This is because many of the aforementioned Promising "primitives"
  are often part of mechanisms that involve communications between async tasks via asyncio.Queue objects and just
  interrupting those promises with KeyboardInterrupt which are extended from BaseException instead of letting
  KeyboardInterrupt to go through the queue leads to hanging of those promises (a queue is waiting for END_OF_QUEUE
  sentinel forever but the task that should send it is dead).
