# MiniAgents

MiniAgents is an asynchronous framework for building LLM-based multi-agent systems in Python, with a focus on immutable messages and token streaming.

## Features

- Asynchronous architecture for efficient and scalable agent interactions
- Token streaming for real-time processing of LLM-generated responses
- Integration with popular LLM providers like OpenAI and Anthropic
- Flexible and extensible design for building custom agents and interactions

## Installation

You can install MiniAgents using pip:

```bash
pip install miniagents
```

## Usage

Here's a basic example of how to use MiniAgents to create a simple dialog between a user agent and an assistant agent:

```python
from miniagents import MiniAgents, miniagent, adialog_loop
from miniagents.ext.console_user_agent import create_console_user_agent
from miniagents.ext.llm.openai import create_openai_agent

async def main():
    user_agent = create_console_user_agent()
    assistant_agent = create_openai_agent(model="gpt-3.5-turbo")

    await adialog_loop(user_agent, assistant_agent)

async with MiniAgents():
    await main()
```

In this example:

1. We create a user agent using `create_console_user_agent()`, which reads user input from the console and writes back to the console.
2. We create an assistant agent using `create_openai_agent()`, specifying the OpenAI model to use (e.g., "gpt-3.5-turbo").
3. We start a dialog loop using `adialog_loop()`, passing the user agent and assistant agent as arguments.
4. The dialog loop runs asynchronously within the `MiniAgents` context, allowing the agents to interact and exchange messages.

## Documentation

For more detailed documentation and examples, please refer to the [MiniAgents documentation](https://miniagents.readthedocs.io/).

## Contributing

Contributions to MiniAgents are welcome! If you find a bug, have a feature request, or want to contribute code, please open an issue or submit a pull request on the [GitHub repository](https://github.com/teremterem/MiniAgents).

## License

MiniAgents is released under the [MIT License](https://opensource.org/licenses/MIT).
