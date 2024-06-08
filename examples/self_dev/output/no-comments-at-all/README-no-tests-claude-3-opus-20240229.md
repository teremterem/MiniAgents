# MiniAgents

MiniAgents is a Python framework for building agent-based systems. It provides a simple and intuitive way to define agents and their interactions.

## Features

- Define agents as simple Python functions decorated with `@miniagent`
- Agents can send and receive messages asynchronously
- Agents can be chained together to form complex interaction flows
- Built-in support for integrating with LLMs like OpenAI and Anthropic
- Promises and async iterators for handling asynchronous operations
- Extensible architecture for adding custom message types and behaviors

## Installation

You can install MiniAgents using pip:

```bash
pip install miniagents
```

## Usage

Here's a simple example of how to define and run agents using MiniAgents:

```python
from miniagents import miniagent, MiniAgents

@miniagent
async def hello_agent(ctx):
    ctx.reply("Hello!")

@miniagent
async def echo_agent(ctx):
    async for msg in ctx.messages:
        ctx.reply(f"You said: {msg}")

async def main():
    await hello_agent.inquire()
    await echo_agent.inquire("How are you?")

if __name__ == "__main__":
    MiniAgents().run(main())
```

This will output:
```
Hello!
You said: How are you?
```

## Integrating with LLMs

MiniAgents provides built-in support for integrating with LLMs like OpenAI and Anthropic. Here's an example of how to use the OpenAI agent:

```python
from miniagents.ext.llm.openai import create_openai_agent

openai_agent = create_openai_agent(model="gpt-4")

async def main():
    response = await openai_agent.inquire("What is the capital of France?")
    print(response)

if __name__ == "__main__":
    MiniAgents().run(main())
```

This will send a prompt to the OpenAI API and print the response.

## Documentation

For more detailed documentation and examples, please refer to the [docs](docs/) directory.

## Contributing

Contributions are welcome! Please see the [contributing guide](CONTRIBUTING.md) for more information.

## License

MiniAgents is released under the [MIT License](LICENSE).
