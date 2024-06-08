# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides abstractions and utilities for defining agents, passing messages between them, and orchestrating their interactions.

## Key Features

- Define agents as simple Python functions decorated with `@miniagent`
- Pass messages between agents using `MessageType` and `MessageSequencePromise`
- Stream messages token-by-token using `MessagePromise` and `MessageTokenStreamer`
- Integrate with LLMs like OpenAI and Anthropic to create AI-powered agents
- Persist messages using `on_persist_message` event handlers
- Compose and chain agents together using utilities like `achain_loop`
- Build on top of the `Promising` library for powerful async programming patterns

## Installation

Install MiniAgents using pip:

```
pip install miniagents
```

## Usage

Here's a simple example of defining an agent and sending it a message:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def echo_agent(ctx: InteractionContext) -> None:
    async for msg in ctx.messages:
        ctx.reply(f"You said: {msg}")

reply = echo_agent.inquire("Hello world!")
print(reply.aresolve_messages())
```

For more examples, see the `examples/` directory.

## Integrations

MiniAgents provides integrations with popular LLMs:

- OpenAI (`miniagents.ext.llm.openai`)
- Anthropic (`miniagents.ext.llm.anthropic`)

These allow you to easily create AI-powered agents. For example:

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent(model="gpt-3.5-turbo")

reply = openai_agent.inquire("What is the capital of France?")
print(reply.aresolve_messages())
```

## Development

MiniAgents is under active development. Contributions are welcome!

Some things to keep in mind when developing MiniAgents:

- Different Promise and StreamedPromise resolvers, piece streamers, appenders and what not should always catch BaseExceptions and not just Exceptions when they capture errors to pass those errors as "pieces" in order for those errors to be raised at the "consumer side". This is because many of the aforementioned Promising "primitives" are often part of mechanisms that involve communications between async tasks via asyncio.Queue objects and just interrupting those promises with KeyboardInterrupt which are extended from BaseException instead of letting KeyboardInterrupt to go through the queue leads to hanging of those promises (a queue is waiting for END_OF_QUEUE sentinel forever but the task that should send it is dead).

## License

MiniAgents is open-source under the MIT License. See LICENSE for more information.
