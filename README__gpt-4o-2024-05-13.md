# 🚀 MiniAgents

A framework on top of asyncio for building LLM-based multi-agent systems in Python, with immutable, Pydantic-based messages and a focus on asynchronous token and message streaming between agents.

## 📦 Installation

```bash
pip install miniagents
```

## 🛠️ Usage

Here's a simple example of how to define an agent:

```python
from miniagents import miniagent, InteractionContext, MiniAgents


@miniagent
async def my_agent(ctx: InteractionContext):
    async for msg_promise in ctx.message_promises:
        ctx.reply(f"You said: {await msg_promise}")


async def amain() -> None:
    async for msg_promise in my_agent.inquire(["Hello", "World"]):
        print(await msg_promise)


if __name__ == "__main__":
    MiniAgents().run(amain())
```

This script will print the following lines to the console:

```
You said: Hello
You said: World
```

### 🔍 Slightly more advanced example

```python
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext


@miniagent
async def agent1(ctx: InteractionContext) -> None:
    print("Agent 1 started")
    ctx.reply("Message from Agent 1")
    print("Agent 1 finished")


@miniagent
async def agent2(ctx: InteractionContext) -> None:
    print("Agent 2 started")
    ctx.reply("Message from Agent 2")
    print("Agent 2 finished")


@miniagent
async def aggregator_agent(ctx: InteractionContext) -> None:
    print("Aggregator agent started")
    ctx.reply([agent1.inquire(), agent2.inquire()])  # caveat: don't use generators here (explained below)
    print("Aggregator agent finished")


async def amain() -> None:
    print("Main function started")
    async for msg_promise in aggregator_agent.inquire():
        print(await msg_promise)
    print("Main function finished")


if __name__ == "__main__":
    MiniAgents().run(amain())
```

This script will print the following lines to the console:

```
Main function started
Aggregator agent started
Aggregator agent finished
Agent 1 started
Agent 1 finished
Agent 2 started
Agent 2 finished
Message from Agent 1
Message from Agent 2
Main function finished
```

The specific order of print statements is due to the asynchronous nature of the agents. The `aggregator_agent` starts and finishes quickly because it immediately replies with the inquiries to `agent1` and `agent2`. These agents then start and finish independently.

### 🧩 Customizing Agent Inquiries

You can start an inquiry with `miniagent.start_inquiry()` and then send messages using `.send_message()` before calling `.reply_sequence()`:

```python
from miniagents import miniagent, InteractionContext, MiniAgents


@miniagent
async def echo_agent(ctx: InteractionContext):
    async for msg_promise in ctx.message_promises:
        ctx.reply(f"Echo: {await msg_promise}")


async def amain() -> None:
    agent_call = echo_agent.start_inquiry()
    agent_call.send_message("First message")
    agent_call.send_message("Second message")
    async for msg_promise in agent_call.reply_sequence():
        print(await msg_promise)


if __name__ == "__main__":
    MiniAgents().run(amain())
```

This script will print:

```
Echo: First message
Echo: Second message
```

### 🧵 Awaiting Message Sequences

You can await the entire `MessageSequencePromise` to resolve it into a tuple of `Message` objects:

```python
from miniagents import miniagent, InteractionContext, MiniAgents


@miniagent
async def echo_agent(ctx: InteractionContext):
    async for msg_promise in ctx.message_promises:
        ctx.reply(f"Echo: {await msg_promise}")


async def amain() -> None:
    reply_sequence = echo_agent.inquire(["Hello", "World"])
    messages = await reply_sequence
    for message in messages:
        print(message.text)


if __name__ == "__main__":
    MiniAgents().run(amain())
```

This script will print:

```
Echo: Hello
Echo: World
```

### 🌐 MiniAgents Context Usage

You can use the `MiniAgents` context in three ways:

1. Calling its `run()` method with your main function as a parameter.
2. Using it as an async context manager.
3. Directly calling its `activate()` (and, potentially, `afinalize()` at the end) methods.

### 🤖 Working with LLMs

MiniAgents provides built-in support for OpenAI and Anthropic language models.

**NOTE:** Make sure to set your OpenAI API key in the `OPENAI_API_KEY` environment variable before running the example below.

```python
from miniagents import MiniAgents
from miniagents.ext.llm.openai import openai_agent

gpt_4o_agent = openai_agent.fork(model="gpt-4o-2024-05-13")


async def amain():
    reply_sequence = gpt_4o_agent.inquire(
        "Hello, how are you?",
        system="You are a helpful assistant.",
        max_tokens=50,
        temperature=0.7,
    )
    async for msg_promise in reply_sequence:
        async for token in msg_promise:
            print(token, end="", flush=True)
        print("\n")


if __name__ == "__main__":
    MiniAgents().run(amain())
```

Even though OpenAI models return a single assistant response, the `openai_agent.inquire()` method is designed to return a sequence of messages that can be streamed token by token. This generalizes to arbitrary agents, making agents in the MiniAgents framework easily interchangeable.

You can read agent responses token-by-token regardless of whether the agent is streaming token by token or returning full messages.

## 📚 Some other pre-packaged agents (`miniagents.ext`)

**NOTE:** Don't forget to set the Anthropic API key.

```python
from miniagents import MiniAgents
from miniagents.ext import dialog_loop, markdown_history_agent
from miniagents.ext.llm import SystemMessage
from miniagents.ext.llm.anthropic import anthropic_agent


async def amain() -> None:
    await dialog_loop.fork(
        assistant_agent=anthropic_agent.fork(model="claude-3-5-sonnet-20240620", max_tokens=1000),
        history_agent=markdown_history_agent,
    ).inquire(
        SystemMessage(
            "Your job is to improve the styling and grammar of the sentences that the user throws at you. "
            "Leave the sentences unchanged if they seem fine."
        )
    )


if __name__ == "__main__":
    MiniAgents().run(amain())
```

Here is what the interaction might look like if you run this script:

```
YOU ARE NOW IN A CHAT WITH AN AI ASSISTANT

Press Enter to send your message.
Press Ctrl+Space to insert a newline.
Press Ctrl+C (or type "exit") to quit the conversation.

USER: hi

ANTHROPIC_AGENT: Hello! The greeting "hi" is a casual and commonly used informal salutation. It's grammatically correct
and doesn't require any changes. If you'd like to provide a more formal or elaborate greeting, you could consider
alternatives such as "Hello," "Good morning/afternoon/evening," or "Greetings."

USER: got it, thanks!

ANTHROPIC_AGENT: You're welcome! The phrase "Got it, thanks!" is a concise and informal way to express understanding and
appreciation. It's perfectly fine as is for casual communication. If you wanted a slightly more formal version, you
could say:

"I understand. Thank you!"

USER:
```

### 🛠️ Implementing a Dialog Loop

For more advanced usage, you can define multiple agents and manage their interactions:

```python
from miniagents import miniagent, InteractionContext, MiniAgents
from miniagents.ext import agent_loop
from miniagents.promising.sentinels import AWAIT


@miniagent
async def user_agent(ctx: InteractionContext) -> None:
    async for msg_promise in ctx.message_promises:
        print("ASSISTANT: ", end="", flush=True)
        async for token in msg_promise:
            print(token, end="", flush=True)
        print()
    ctx.reply(input("USER: "))


@miniagent
async def assistant_agent(ctx: InteractionContext) -> None:
    aggregated_message = await ctx.message_promises.as_single_promise()
    ctx.reply(f'You said "{aggregated_message}"')


async def amain() -> None:
    await agent_loop.fork(agents=[user_agent, AWAIT, assistant_agent]).inquire()


if __name__ == "__main__":
    MiniAgents().run(amain())
```

Output:

```
USER: hi
ASSISTANT: You said "hi"
USER: nice!
ASSISTANT: You said "nice!"
USER: bye
ASSISTANT: You said "bye"
USER:
```

The `AWAIT` sentinel is used to indicate that the agent should wait for the previous agent to finish before proceeding.

### 📝 Custom Message Models

You can create custom message types by subclassing `Message`.

```python
from miniagents.messages import Message


class CustomMessage(Message):
    custom_field: str


message = CustomMessage(text="Hello", custom_field="Custom Value")
print(message.text)  # Output: Hello
print(message.custom_field)  # Output: Custom Value
```

### 📦 Existing Message Models

```python
from miniagents.ext.llm import UserMessage, SystemMessage, AssistantMessage

user_message = UserMessage(text="Hello!")
system_message = SystemMessage(text="System message")
assistant_message = AssistantMessage(text="Assistant message")
```

For more advanced usage, check out the [examples](examples/) directory.

## 💡 Motivation

There are three main features of MiniAgents that motivated the creation of this framework:

1. **Asynchronous Token Streaming**: Built around supporting asynchronous token streaming across chains of interconnected agents.
2. **Hierarchical Message Resolution**: Easily throw bare strings, messages, message promises, collections, and sequences of messages and message promises into an agent reply. The entire hierarchical structure is asynchronously resolved into a flat and uniform sequence of message promises.
3. **Start ASAP Mode**: Agents work in `start_asap` mode by default, actively seeking every opportunity to proceed with processing in the background when async tasks switch.

The third feature combines this `start_asap` approach with regular async/await and async generators by using streamed promises designed to be "replayable."

Messages are immutable once created to ensure consistency and reliability.

### 📝 Persisting Messages

Use the `@MiniAgents().on_persist_message` decorator to persist messages as they are sent/received. Messages have a `hash_key` property that calculates the SHA-256 of the content, used as the ID of the `Messages`.

## 🔧 Features

- Define agents as simple Python functions decorated with `@miniagent`
- Integrate with OpenAI and Anthropic LLMs using `openai_agent` and `anthropic_agent`
- Built on top of the `Promising` library for managing asynchronous operations
- Asynchronous promise-based programming model with `Promise` and `StreamedPromise`
- Hooks to persist messages as they are sent/received
- Typing with Pydantic for validation and serialization of messages

## 📚 Documentation

### 📂 Modules

The framework is organized into several modules:

- `miniagents`: Core functionality
- `miniagents.ext`: Extensions, including LLM integrations and utility agents
- `miniagents.promising`: Promise-based asynchronous programming utilities

### 📖 Core Concepts

- **Agents**: Functions decorated with `@miniagent` that handle interactions.
- **Messages**: Immutable, Pydantic-based objects used for communication between agents.
- **Promises**: Asynchronous constructs for handling token and message streaming.

## 📜 License

MiniAgents is released under the [MIT License](LICENSE).

## ❓ FAQ

**Q: What is the purpose of the `start_asap` mode?**

A: The `start_asap` mode allows agents to actively seek every opportunity to proceed with processing in the background when async tasks switch, improving efficiency and responsiveness.

**Q: How do I persist messages?**

A: Use the `@MiniAgents().on_persist_message` decorator to persist messages as they are sent/received.

**Q: Can I integrate other LLMs?**

A: Yes, MiniAgents provides built-in support for OpenAI and Anthropic language models, and you can add other integrations as needed.

## 🤝 Contributing

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders, and other components should always catch BaseExceptions and not just Exceptions**. This is because many of these components involve communications between async tasks via asyncio.Queue objects. Interrupting these promises with KeyboardInterrupt (which extends from BaseException) instead of letting it go through the queue can lead to hanging promises (a queue waiting for END_OF_QUEUE sentinel forever while the task that should send it is dead).

---

Happy coding with MiniAgents! 🚀
