# 🤖 MiniAgents

A framework on top of asyncio for building LLM-based multi-agent systems in Python, with immutable, Pydantic-based
messages and a focus on asynchronous token and message streaming between agents.

## 🚀 Installation

```bash
pip install miniagents
```

## 📚 Usage

Here's a simple example of how to define an agent:

```python
from miniagents import miniagent, InteractionContext, MiniAgents


@miniagent
async def my_agent(ctx: InteractionContext):
    async for msg_promise in ctx.message_promises:
        ctx.reply(f"You said: {await msg_promise}")


async def main() -> None:
    async for msg_promise in my_agent.inquire(["Hello", "World"]):
        print(await msg_promise)


if __name__ == "__main__":
    MiniAgents().run(main())
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
    ctx.reply([agent1.inquire(), agent2.inquire()])
    print("Aggregator agent finished")


async def main() -> None:
    print("Main function started")
    async for msg_promise in aggregator_agent.inquire():
        print(await msg_promise)
    print("Main function finished")


if __name__ == "__main__":
    MiniAgents().run(main())
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

The order of the print statements is determined by the asynchronous nature of the agents. Here's what happens:

1. The main function starts and calls `aggregator_agent.inquire()`.
2. The aggregator agent starts and schedules `agent1.inquire()` and `agent2.inquire()` to run concurrently by wrapping them in a list.
3. The aggregator agent finishes immediately after scheduling the sub-agents.
4. `agent1` and `agent2` start running concurrently.
5. `agent1` finishes and sends its message.
6. `agent2` finishes and sends its message.
7. The main function receives the messages from `agent1` and `agent2` in the order they finished.
8. The main function finishes.

Here's a simple example that demonstrates how to use `miniagent.start_inquiry()`, `.send_message()`, and `.reply_sequence()`:

```python
from miniagents import miniagent, InteractionContext, MiniAgents


@miniagent
async def echo_agent(ctx: InteractionContext):
    async for msg_promise in ctx.message_promises:
        ctx.reply(f"You said: {await msg_promise}")


async def main() -> None:
    inquiry = echo_agent.start_inquiry()
    inquiry.send_message("Hello")
    inquiry.send_message("World")
    async for msg_promise in inquiry.reply_sequence():
        print(await msg_promise)


if __name__ == "__main__":
    MiniAgents().run(main())
```

This script will print the following lines to the console:

```
You said: Hello
You said: World
```

You can also `await` the whole `MessageSequencePromise`, resolving it into a tuple of `Message` objects:

```python
from miniagents import miniagent, InteractionContext, MiniAgents


@miniagent
async def echo_agent(ctx: InteractionContext):
    async for msg_promise in ctx.message_promises:
        ctx.reply(f"You said: {await msg_promise}")


async def main() -> None:
    messages = await echo_agent.inquire(["Hello", "World"])
    print(messages)


if __name__ == "__main__":
    MiniAgents().run(main())
```

This script will print a tuple of `Message` objects:

```
(Message(text='You said: Hello'), Message(text='You said: World'))
```

The `MiniAgents` context can be used in three ways:

1. Calling its `run()` method with your main function as a parameter (as shown in the examples above).
2. Using it as an async context manager:

```python
async def main() -> None:
    async with MiniAgents():
        # your code here
```

3. Directly calling its `activate()` and `afinalize()` methods:

```python
async def main() -> None:
    mini_agents = MiniAgents()
    mini_agents.activate()
    try:
        # your code here
    finally:
        await mini_agents.afinalize()
```

### 🌐 Work with LLMs

MiniAgents provides built-in support for OpenAI and Anthropic language models (with possibility to add other
integrations).

**NOTE:** Make sure to set your OpenAI API key in the `OPENAI_API_KEY` environment variable before running the example
below.

```python
from miniagents import MiniAgents
from miniagents.ext.llm.openai import openai_agent

# NOTE: "Forking" an agent is a convenience method that creates a new agent instance with the specified configuration.
# Alternatively, you could just call `openai_agent.inquire()` directly and pass the model parameter every time.
gpt_4o_agent = openai_agent.fork(model="gpt-4o-2024-05-13")


async def main():
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
    MiniAgents().run(main())
```

Even though OpenAI models return a single assistant response, the `openai_agent.inquire()` method is designed to return a sequence of messages (which is a sequence of message promises) that can be streamed token by token. This generalizes to arbitrary agents, making agents in the MiniAgents framework easily interchangeable (agents in this framework support sending and receiving zero or more messages).

You can read agent responses token-by-token as shown above regardless of whether the agent is streaming token by token or returning full messages (the complete message text will just be returned as a single "token" in the latter case).

## 🧰 Some other pre-packaged agents (`miniagents.ext`)

**NOTE:** Don't forget to set the Anthropic API key in the `ANTHROPIC_API_KEY` environment variable before running the example below.

```python
from miniagents import MiniAgents
from miniagents.ext import dialog_loop, markdown_history_agent
from miniagents.ext.llm import SystemMessage
from miniagents.ext.llm.anthropic import anthropic_agent


async def main() -> None:
    await dialog_loop.fork(
        assistant_agent=anthropic_agent.fork(model="claude-3-5-sonnet-20240620", max_tokens=1000),
        # write chat history to a markdown file (by default - `CHAT.md` in the current working directory,
        # "fork" this agent to customize)
        history_agent=markdown_history_agent,
    ).inquire(
        SystemMessage(
            "Your job is to improve the styling and grammar of the sentences that the user throws at you. "
            "Leave the sentences unchanged if they seem fine."
        )
    )


if __name__ == "__main__":
    MiniAgents().run(main())
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

The `dialog_loop` agent is a pre-built agent that facilitates a dialog between the user and an assistant agent. It uses the `user_agent` to prompt the user for input and the `console_echo_agent` to display the assistant's responses.

The `markdown_history_agent` is an agent that logs the conversation history to a markdown file. It appends each message to the file, prefixing it with the role of the sender (user or assistant).

Other useful agents in `miniagents.ext` include:

- `console_echo_agent`: Echoes messages to the console token by token.
- `console_prompt_agent`: Prompts the user for input in the console.
- `user_agent`: A user agent that echoes messages from the agent that called it, reads the user input, and then returns the full chat history as a reply.
- `in_memory_history_agent`: An agent that keeps track of the chat history in memory.

Feel free to explore the source code in the `miniagents.ext` package to see how various agents are implemented and to get ideas for building your own custom agents!

### 🛠️ Here is how you can implement a dialog loop yourself from ground up

For more advanced usage, you can define multiple agents and manage their interactions (for simplicity, there is no
history agent in this particular example, checkout `in_memory_history_agent` and how it is used if you're interested):

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


async def main() -> None:
    await agent_loop.fork(agents=[user_agent, AWAIT, assistant_agent]).inquire()


if __name__ == "__main__":
    MiniAgents().run(main())
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

The `AWAIT` sentinel is used to indicate that the `assistant_agent` should wait for the `user_agent` to finish before processing the user's message. This ensures that the messages are processed in the correct order, alternating between the user and the assistant.

### 🎨 Custom Message models

You can create custom message types by subclassing `Message`.

```python
from miniagents.messages import Message


class CustomMessage(Message):
    custom_field: str


message = CustomMessage(text="Hello", custom_field="Custom Value")
print(message.text)  # Output: Hello
print(message.custom_field)  # Output: Custom Value
```

### 📨 Existing Message models

```python
from miniagents.ext.llm import UserMessage, SystemMessage, AssistantMessage

user_message = UserMessage(text="Hello!")
system_message = SystemMessage(text="System message")
assistant_message = AssistantMessage(text="Assistant message")
```

---

For more advanced usage, check out the [examples](examples/) directory.

## 💡 What was the motivation behind this project?

There are three main features of MiniAgents the idea of which motivated the creation of this framework:

1. It is built around supporting asynchronous token streaming across chains of interconnected agents, making this the
   core feature of the framework.
2. It is very easy to throw bare strings, messages, message promises, collections, and sequences of messages and message
   promises (as well as the promises of the sequences themselves) all together into an agent reply (see `MessageType`).
   This entire hierarchical structure will be asynchronously resolved in the background into a flat and uniform sequence
   of message promises (it will be automatically "flattened" in the background).
3. By default, agents work in so called `start_asap` mode, which is different from the usual way coroutines work where
   you need to actively await on them and/or iterate over them (in case of asynchronous generators). In `start_asap`
   mode, every agent, after it was invoked, actively seeks every opportunity to proceed its processing in the background
   when async tasks switch.

The third feature combines this `start_asap` approach with regular async/await and async generators by using so called
streamed promises (see `StreamedPromise` and `Promise` classes) which were designed to be "replayable" by nature.

It was chosen for messages to be immutable once they are created (see `Message` and `Frozen` classes) in order to make
all of the above possible (because this way there are no concerns about the state of the message being changed in the
background).

The `@MiniAgents().on_persist_message` decorator allows you to persist messages as they are sent/received. Messages (as well as any other Pydantic models derived from `Frozen`) have a `hash_key` property that calculates the sha256 hash of the content of the message. This hash key is used as the id of the `Messages` (or any other `Frozen` model), much like there are commit hashes in git.

## 🌟 Some other features

- Define agents as simple Python functions decorated with `@miniagent`
- Integrate with OpenAI and Anthropic LLMs using `openai_agent` and `anthropic_agent`
- Built on top of the `Promising` library (which is a library built directly inside this library 🙂) for managing
  asynchronous operations
- Asynchronous promise-based programming model with `Promise` and `StreamedPromise`
- Hooks to persist messages as they are sent/received
- Typing with Pydantic for validation and serialization of messages

## 📖 Documentation

### 📦 Modules

The MiniAgents framework is organized into the following main modules:

- `miniagents`: The core module containing the main classes and functions of the framework.
  - `miniagents.miniagents`: Contains the `MiniAgents` context manager class and the `miniagent` decorator.
  - `miniagents.messages`: Contains the `Message` class and related classes for working with messages.
  - `miniagents.promising`: Contains the `Promise` and `StreamedPromise` classes for asynchronous programming.
- `miniagents.ext`: Contains pre-built agents and utilities for common use cases.
  - `miniagents.ext.llm`: Contains agents for working with large language models (OpenAI, Anthropic).
  - `miniagents.ext.agent_aggregators`: Contains agents for aggregating and chaining other agents.
  - `miniagents.ext.history_agents`: Contains agents for managing conversation history.
  - `miniagents.ext.misc_agents`: Contains miscellaneous utility agents.

### 🧠 Core Concepts

- **Agent**: A function decorated with `@miniagent` that defines the behavior of an agent in the system.
- **Message**: An immutable data object representing a message passed between agents. Messages can contain text, metadata, and references to other messages.
- **Promise**: An asynchronous programming construct representing a value that may not be available yet. Promises allow agents to work with values that are not immediately available without blocking execution.
- **StreamedPromise**: A special type of promise that represents a value that can be streamed piece by piece. This is useful for streaming responses from LLMs token by token.
- **MessageSequence**: A flattened sequence of messages that can contain nested sequences, promises, and other message types. MessageSequences are automatically resolved into a flat sequence of message promises.
- **InteractionContext**: An object passed to an agent function that provides access to the incoming messages and allows the agent to send replies.
- **MiniAgents**: The main context manager class that manages the lifecycle of agents and provides configuration options for the framework.

## 📜 License

MiniAgents is released under the [MIT License](../../../LICENSE).

## 🙋 FAQ

**Q: How do I install MiniAgents?**

A: You can install MiniAgents using pip:

```bash
pip install miniagents
```

**Q: How do I define a custom agent?**

A: To define a custom agent, create a function and decorate it with `@miniagent`. The function should take an `InteractionContext` object as its parameter. For example:

```python
from miniagents import miniagent, InteractionContext

@miniagent
async def my_custom_agent(ctx: InteractionContext):
    async for msg_promise in ctx.message_promises:
        # Process the incoming message
        response = f"You said: {await msg_promise}"
        ctx.reply(response)
```

**Q: How do I run the MiniAgents framework?**

A: To run the MiniAgents framework, create an instance of the `MiniAgents` class and use it as a context manager. Then, call the `inquire()` method on your agent to start the interaction. For example:

```python
from miniagents import MiniAgents

async def main():
    async for msg_promise in my_custom_agent.inquire("Hello!"):
        print(await msg_promise)

if __name__ == "__main__":
    MiniAgents().run(main())
```

**Q: Can I use MiniAgents with other asynchronous libraries?**

A: Yes, MiniAgents is built on top of the standard `asyncio` library and should be compatible with other asynchronous libraries that work with `asyncio`.

## 🤝 Some note(s) for contributors

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders and what not should always catch
  BaseExceptions and not just Exceptions** when they capture errors to pass those errors as "pieces" in order for
  those errors to be raised at the "consumer side". This is because many of the aforementioned Promising "primitives"
  are often part of mechanisms that involve communications between async tasks via asyncio.Queue objects and just
  interrupting those promises with KeyboardInterrupt which are extended from BaseException instead of letting
  KeyboardInterrupt to go through the queue leads to hanging of those promises (a queue is waiting for END_OF_QUEUE
  sentinel forever but the task that should send it is dead).

---

Happy coding with MiniAgents! 🚀
