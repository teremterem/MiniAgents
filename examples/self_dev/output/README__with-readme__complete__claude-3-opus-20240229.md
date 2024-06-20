Here's a README.md for your MiniAgents framework:

# MiniAgents

MiniAgents is a Python framework for building agent-based systems with a focus on immutable messages and token streaming. It provides a simple and intuitive way to define agents and their interactions, and integrates with large language models (LLMs) like OpenAI and Anthropic.

## Features

- Define agents as simple Python functions decorated with `@miniagent`
- Agents can interact with each other by sending and receiving messages
- Agents can send and receive messages asynchronously
- Agents can run in parallel and communicate with each other
- Promises and async iterators are used extensively to enable non-blocking communication
- Pass messages between agents using `MessageType` objects
- Integrate with OpenAI and Anthropic LLMs using `create_openai_agent` and `create_anthropic_agent`
- Stream tokens from LLMs piece-by-piece using `StreamedPromise`
- Flatten nested message sequences with `MessageSequence`
- Immutable message passing via `Frozen` pydantic models
- Hooks to persist messages as they are sent/received

## Installation

Install MiniAgents using pip:

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

### Integrating with OpenAI

To create an agent that interacts with OpenAI:

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent()

# Running the OpenAI agent
mini_agents.run(openai_agent.inquire("Hello, OpenAI!"))
```

### Integrating with Anthropic

Similarly, you can create an agent that interacts with Anthropic:

```python
from miniagents.ext.llm.anthropic import create_anthropic_agent

anthropic_agent = create_anthropic_agent()

# Running the Anthropic agent
mini_agents.run(anthropic_agent.inquire("Hello, Anthropic!"))
```

## Documentation

The key classes and concepts in MiniAgents include:

- `MiniAgents`: The main context manager for running agents
- `@miniagent`: Decorator for defining agents
- `InteractionContext`: Passed to agent functions, provides methods for replying and finishing early
- `Message`: Represents a message passed between agents
- `MessagePromise`: A promise that resolves to a message
- `StreamedPromise`: Represents a promise of a whole value that can be streamed piece by piece

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md for details.

## License

MiniAgents is released under the MIT License.

---

This README provides an overview of the MiniAgents framework, its features, installation instructions, basic usage examples, and key concepts. The examples demonstrate how to define agents, have them interact, and integrate with OpenAI and Anthropic LLMs.

Let me know if you would like me to expand or modify any part of the README further. I'm happy to iterate on it to best document your framework.
