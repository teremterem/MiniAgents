# MiniAgents

MiniAgents is a Python framework for building multi-agent systems with a focus on natural language processing and large language models (LLMs). It provides abstractions and utilities for defining agents, managing their interactions, and integrating with various LLM providers.

## Key Features

- Define agents as simple Python functions decorated with `@miniagent`
- Agents can interact with each other by sending and receiving messages
- Supports streaming of messages and tokens for efficient processing
- Seamless integration with OpenAI and Anthropic LLM APIs
- Utilities for working with message sequences, splitting and joining messages
- Built on top of the `Promising` library for managing asynchronous operations

## Installation

You can install MiniAgents using pip:

```
pip install miniagents
```

## Usage

Here's a simple example of defining agents and having them interact:

```python
from miniagents import miniagent, MiniAgents, InteractionContext

@miniagent
async def agent1(ctx: InteractionContext):
    ctx.reply("Hello from Agent 1!")

@miniagent
async def agent2(ctx: InteractionContext):
    message = await ctx.messages.aresolve_messages()
    ctx.reply(f"Agent 2 received: {message[0].text}")

async def main():
    async with MiniAgents():
        agent2_replies = agent2.inquire(agent1.inquire())
        print(await agent2_replies.aresolve_messages())

asyncio.run(main())
```

This will output:
```
(Message(text='Agent 2 received: Hello from Agent 1!'),)
```

For more advanced usage, including integration with LLMs, see the documentation and examples.

## Documentation

TODO: Add link to documentation

## Contributing

Contributions are welcome! Please see the contributing guidelines for more information.

## License

MiniAgents is released under the MIT License.

## Things to remember (for the developer of this framework)

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders and what not should always catch
  BaseExceptions and not just Exceptions** when they capture errors to pass those errors as "pieces" in order for
  those errors to be raised at the "consumer side". This is because many of the aforementioned Promising "primitives"
  are often part of mechanisms that involve communications between async tasks via asyncio.Queue objects and just
  interrupting those promises with KeyboardInterrupt which are extended from BaseException instead of letting
  KeyboardInterrupt to go through the queue leads to hanging of those promises (a queue is waiting for END_OF_QUEUE
  sentinel forever but the task that should send it is dead).
