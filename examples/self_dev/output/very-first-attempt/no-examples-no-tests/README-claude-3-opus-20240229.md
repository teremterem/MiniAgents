# MiniAgents

MiniAgents is a Python framework for building and interacting with AI agents. It provides a simple and intuitive way to define agents, chain them together, and facilitate communication between them using messages.

## Key Features

- Define agents as simple Python functions decorated with `@miniagent`
- Chain agents together using `achain_loop` for sequential interactions
- Agents communicate via `Message` objects which can be streamed token by token
- `MessagePromise` and `MessageSequencePromise` allow for asynchronous message handling
- Integrates with Anthropic and OpenAI language models out of the box
- Extensible design to support other language models and custom agent implementations

## Installation

You can install MiniAgents using pip:

```
pip install miniagents
```

## Basic Usage

Here's a simple example of defining an agent and interacting with it:

```python
from miniagents import miniagent, Message

@miniagent
async def hello_agent(ctx):
    ctx.reply(Message(text="Hello, how can I assist you today?"))

messages = hello_agent.inquire()
print(await messages.aresolve_messages())
```

This will output:

```
(Message(text='Hello, how can I assist you today?'),)
```

## Chaining Agents

You can chain multiple agents together using `achain_loop`:

```python
from miniagents import miniagent, Message, achain_loop, AWAIT

@miniagent
async def agent1(ctx):
    ctx.reply(Message(text="Agent 1 says hi!"))

@miniagent
async def agent2(ctx):
    ctx.reply(Message(text="Agent 2 says hello!"))

await achain_loop([agent1, AWAIT, agent2])
```

This will make `agent1` and `agent2` take turns interacting, with each agent receiving the messages from the previous agent.

## Language Model Integration

MiniAgents comes with built-in support for Anthropic and OpenAI language models. You can create agents backed by these models like this:

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent(model="gpt-3.5-turbo")
messages = openai_agent.inquire(Message(text="What is the capital of France?"))
print(await messages.aresolve_messages())
```

This will query the OpenAI model and print its response.

## Documentation

For more details on how to use MiniAgents, please refer to the documentation (TODO: link to docs).

## Contributing

Contributions are welcome! Please see the contributing guide (TODO: link to contributing guide) for more information.

## License

MiniAgents is released under the MIT License. See LICENSE for details.
