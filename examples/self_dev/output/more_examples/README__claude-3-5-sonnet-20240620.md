Certainly! I'll create a comprehensive README that incorporates both the existing examples and use cases, as well as new ones that were missed in the previous versions. Here's an improved README for the MiniAgents framework:

# MiniAgents

MiniAgents is an asynchronous Python framework for building LLM-based multi-agent systems, with a focus on immutable messages and token streaming. It provides a simple and intuitive way to define agents and their interactions, making it easier to build complex systems that rely on asynchronous interactions and streaming data.

## Features

- **Agent Management**: Easily create, manage, and chain multiple agents.
- **Asynchronous Communication**: Enables non-blocking interactions between agents and LLMs.
- **Immutability**: Ensures predictable and reproducible agent behavior through immutable messages.
- **Streaming**: Supports efficient processing of large language model outputs via token streaming.
- **LLM Integration**: Seamlessly integrate with popular LLMs like OpenAI and Anthropic.
- **Message Handling**: Robust message handling with support for nested messages and promises.
- **Chat History**: Manage chat history with support for in-memory and markdown file storage.
- **Extensibility**: Flexible architecture allows integration with various LLM providers and custom agents.

## Installation

```bash
pip install miniagents
```

## Basic Usage

Here's a simple example of using MiniAgents to create a dialog between a user and an AI assistant powered by OpenAI's GPT-3.5-turbo model:

```python
import asyncio
from dotenv import load_dotenv
from miniagents.ext.llm.openai import openai_agent
from miniagents.ext.misc_agents import console_user_agent
from miniagents.utils import adialog_loop
from miniagents.miniagents import MiniAgents

load_dotenv()

async def main():
    assistant_agent = openai_agent.fork(model="gpt-3.5-turbo")

    async with MiniAgents():
        await adialog_loop(console_user_agent, assistant_agent)

if __name__ == "__main__":
    asyncio.run(main())
```

This will start an interactive dialog where the user can chat with the AI assistant in the console.

## Advanced Usage

### Custom Agents

You can define custom agents using the `@miniagent` decorator:

```python
from miniagents.miniagents import miniagent, InteractionContext

@miniagent
async def my_agent(ctx: InteractionContext):
    async for message in ctx.message_promises:
        ctx.reply(f"You said: {message}")
```

### Chaining Agents

You can chain multiple agents together:

```python
from miniagents.miniagents import MiniAgents, miniagent
from miniagents.utils import achain_loop
from miniagents.promising.sentinels import AWAIT

@miniagent
async def agent1(ctx):
    ctx.reply("Hello from Agent 1!")

@miniagent
async def agent2(ctx):
    async for msg in ctx.message_promises:
        ctx.reply(f"Agent 2 received: {msg}")

async def main():
    async with MiniAgents():
        await achain_loop([agent1, AWAIT, agent2])

asyncio.run(main())
```

### Error Handling

MiniAgents treats exceptions in agents as messages, allowing for graceful error handling:

```python
@miniagent
async def error_prone_agent(ctx):
    try:
        # Some operation that might raise an exception
        result = await some_risky_operation()
        ctx.reply(f"Operation successful: {result}")
    except Exception as e:
        ctx.reply(f"An error occurred: {str(e)}")
```

### Custom Message Types

You can create custom message types by subclassing `Message`:

```python
from miniagents.messages import Message

class CustomMessage(Message):
    custom_field: str

message = CustomMessage(text="Hello", custom_field="Custom Value")
print(message.text)  # Output: Hello
print(message.custom_field)  # Output: Custom Value
```

### Streaming Tokens from LLMs

MiniAgents supports token streaming from Language Models:

```python
from miniagents.ext.llm.openai import openai_agent
from miniagents.miniagents import MiniAgents

async def main():
    async with MiniAgents():
        llm_agent = openai_agent.fork(model="gpt-3.5-turbo")
        response = llm_agent.inquire("Tell me a short story", stream=True)
        async for msg_promise in response:
            async for token in msg_promise:
                print(token, end="", flush=True)
            print()

asyncio.run(main())
```

### Persisting Chat History

You can persist chat history using the `markdown_history_agent`:

```python
from miniagents.ext.history_agents import markdown_history_agent
from miniagents.ext.llm.openai import openai_agent
from miniagents.ext.misc_agents import console_user_agent
from miniagents.utils import adialog_loop

async def main():
    async with MiniAgents():
        await adialog_loop(
            user_agent=console_user_agent,
            assistant_agent=openai_agent.fork(model="gpt-3.5-turbo"),
            history_agent=markdown_history_agent.fork(history_md_file="chat_history.md")
        )

asyncio.run(main())
```

### Parallel Execution of Agents

MiniAgents supports parallel execution of agents:

```python
from miniagents.miniagents import MiniAgents, miniagent

@miniagent
async def parallel_agent(ctx):
    # Some time-consuming operation
    await asyncio.sleep(1)
    ctx.reply("Done!")

async def main():
    async with MiniAgents():
        tasks = [parallel_agent.inquire() for _ in range(5)]
        await asyncio.gather(*tasks)

asyncio.run(main())
```

### Using AWAIT and CLEAR Sentinels

The `AWAIT` and `CLEAR` sentinels can be used to control the flow of execution in agent chains:

```python
from miniagents.miniagents import MiniAgents, miniagent
from miniagents.utils import achain_loop
from miniagents.promising.sentinels import AWAIT, CLEAR

@miniagent
async def agent1(ctx):
    ctx.reply("Message from Agent 1")

@miniagent
async def agent2(ctx):
    ctx.reply("Message from Agent 2")

async def main():
    async with MiniAgents():
        await achain_loop([agent1, AWAIT, agent2, CLEAR, agent1])

asyncio.run(main())
```

### Extending the Framework

You can extend MiniAgents by creating custom agents or integrating with new LLM providers:

```python
from miniagents.miniagents import miniagent, InteractionContext
from miniagents.messages import Message

@miniagent
async def custom_llm_agent(ctx: InteractionContext, custom_llm_client):
    async for message in ctx.message_promises:
        response = await custom_llm_client.generate(str(message))
        ctx.reply(Message(text=response))
```

## Advanced Concepts

### Message Promises and Sequences

MiniAgents uses `MessagePromise` and `MessageSequencePromise` for handling asynchronous message operations:

```python
from miniagents.messages import Message, MessageSequencePromise
from miniagents.miniagents import MiniAgents

async def process_messages(messages: MessageSequencePromise):
    async for msg_promise in messages:
        message = await msg_promise
        print(f"Processed: {message.text}")

async def main():
    async with MiniAgents():
        messages = MessageSequencePromise(
            prefill_pieces=[
                Message(text="Hello"),
                Message(text="World")
            ]
        )
        await process_messages(messages)

asyncio.run(main())
```

### Self-Development Capabilities

MiniAgents includes self-development features, allowing agents to improve themselves or generate new code:

```python
from miniagents.ext.llm.openai import openai_agent
from miniagents.miniagents import MiniAgents, miniagent

@miniagent
async def self_improving_agent(ctx):
    current_code = "def greet(name):\n    print(f'Hello, {name}!')"

    improvement_prompt = f"Improve the following Python function:\n\n{current_code}\n\nAdd error handling and make it more versatile."

    improved_code = await openai_agent.inquire(improvement_prompt)

    ctx.reply(f"Improved code:\n\n{improved_code}")

async def main():
    async with MiniAgents():
        await self_improving_agent.inquire()

asyncio.run(main())
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](LICENSE).

---

This README now provides a more comprehensive overview of the MiniAgents framework, including both basic and advanced usage examples, as well as explanations of key concepts that were missing from previous versions. It showcases the framework's capabilities in areas such as custom agents, error handling, message types, token streaming, chat history persistence, parallel execution, and extensibility.
