# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides abstractions and utilities for defining agents, passing messages between them, and integrating with large language models (LLMs) like OpenAI and Anthropic.

## Key Features

- Define agents as simple Python functions decorated with `@miniagent`
- Pass messages between agents using `MessageType` objects
- Integrate with OpenAI and Anthropic LLMs using `create_openai_agent` and `create_anthropic_agent`
- Stream tokens from LLMs piece-by-piece using `StreamedPromise`
- Flatten nested message sequences with `MessageSequence`
- Immutable data models using `Frozen` base class
- Asynchronous promise-based programming model with `Promise` and `StreamedPromise`
- Manage async context and lifecycle with `PromisingContext`

## Installation

Install using pip:

```
pip install miniagents
```

## Usage

Here's a simple example of defining agents and passing messages:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def hello_agent(ctx: InteractionContext):
    ctx.reply("Hello!")

@miniagent
async def echo_agent(ctx: InteractionContext):
    async for msg in ctx.messages:
        ctx.reply(f"You said: {msg}")

# Pass a message from hello_agent to echo_agent
reply = hello_agent.inquire()
echo_agent.inquire(reply)
```

And here's how to integrate with an OpenAI LLM:

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent(model="gpt-3.5-turbo")

reply = openai_agent.inquire(
    "What is the capital of France?",
    stream=True,
    max_tokens=50
)

async for token in reply:
    print(token, end='', flush=True)
```

## Testing

Run tests using pytest:

```
pytest tests/
```

## Contributing

Contributions are welcome! Please submit a pull request.

## License

MiniAgents is open-source under the MIT license.
