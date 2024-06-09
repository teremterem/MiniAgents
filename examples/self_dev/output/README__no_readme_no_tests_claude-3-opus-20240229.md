# MiniAgents

MiniAgents is a Python framework for building agent-based systems and integrating with large language models (LLMs) such as OpenAI's GPT models and Anthropic's Claude.

## Features

- Lightweight and flexible agent-based architecture
- Easy integration with OpenAI and Anthropic LLMs
- Streaming support for efficient token-by-token processing
- Asynchronous programming model using async/await syntax
- Promises and message passing for communication between agents
- Utilities for working with messages and agent interactions

## Installation

You can install MiniAgents using Poetry:

```bash
poetry add miniagents
```

## Usage

Here's a basic example of how to use MiniAgents to interact with an OpenAI LLM:

```python
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.miniagents import MiniAgents

async def amain():
    llm_agent = create_openai_agent(model="gpt-4")

    reply_sequence = llm_agent.inquire(
        "How are you today?",
        max_tokens=1000,
        temperature=0.0,
        system="Respond only in Yoda-speak.",
    )

    async for msg_promise in reply_sequence:
        async for token in msg_promise:
            print(token, end="", flush=True)

if __name__ == "__main__":
    MiniAgents().run(amain())
```

This example creates an OpenAI agent, sends a message to it, and prints the response token by token.

## Documentation

TODO: Add a link to the full documentation.

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue on the [GitHub repository](https://github.com/teremterem/MiniAgents). If you'd like to contribute code, please fork the repository and submit a pull request.

## License

MiniAgents is released under the [MIT License](LICENSE).

## Acknowledgements

MiniAgents was inspired by various agent-based frameworks and LLM integration libraries. Special thanks to the developers and communities behind those projects.

---

This README provides an overview of the MiniAgents framework based on the source files you provided. It includes sections on features, installation, usage, documentation, contributing, license, and acknowledgements. You can further expand and customize the README as needed to provide more detailed information about your framework.
