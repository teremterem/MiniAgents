# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides a simple and flexible way to create agents that can interact with each other and with external systems.

## Features

- Define agents as simple Python functions decorated with `@miniagent`
- Agents can send and receive messages asynchronously
- Support for streaming messages piece by piece (e.g. token by token)
- Agents can be chained together to form pipelines or loops
- Integration with large language models (LLMs) like OpenAI's GPT and Anthropic's Claude
- Promises and async/await for managing asynchronous operations
- Persistence of agent interactions (messages can be automatically saved)
- Typing with Pydantic for validation and serialization of messages

## Installation

You can install MiniAgents using pip:

```bash
pip install miniagents
```

## Usage

Here's a simple example of how to define and use agents in MiniAgents:

```python
from miniagents import miniagent, MiniAgents, InteractionContext

@miniagent
async def hello_agent(ctx: InteractionContext):
    async for msg in ctx.messages:
        name = await msg
        ctx.reply(f"Hello, {name}!")

@miniagent
async def goodbye_agent(ctx: InteractionContext):
    async for msg in ctx.messages:
        name = await msg
        ctx.reply(f"Goodbye, {name}!")

async def main():
    async with MiniAgents():
        reply = hello_agent.inquire("Alice")
        reply = goodbye_agent.inquire(reply)
        print(await reply)

if __name__ == "__main__":
    MiniAgents().run(main())
```

This will output:
```
Hello, Alice!
Goodbye, Hello, Alice!!
```

## Integrations

MiniAgents provides integrations with popular LLMs:

- OpenAI's GPT models via `miniagents.ext.llm.openai`
- Anthropic's Claude models via `miniagents.ext.llm.anthropic`

You can easily create agents backed by these LLMs and incorporate them into your agent systems.

## Documentation

TODO: Add link to documentation.

## Contributing

Contributions are welcome! Please see the contributing guide for details.

## License

MiniAgents is open-source software licensed under the MIT license. See LICENSE for details.
