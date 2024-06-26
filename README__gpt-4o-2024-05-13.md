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

### 🤖 Work with LLMs

MiniAgents provides built-in support for OpenAI and Anthropic language models with the possibility to add other integrations.

⚠️ **ATTENTION!** Make sure to set your OpenAI API key in the `OPENAI_API_KEY` environment variable before running the example below. ⚠️

```python
from miniagents import MiniAgents
from miniagents.ext.llm.openai import openai_agent

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

Even though OpenAI models return a single assistant response, the `openai_agent.inquire()` method is designed to return a sequence of messages (which is a sequence of message promises) that can be streamed token by token. This generalizes to arbitrary agents, making agents in the MiniAgents framework easily interchangeable. Agents in this framework support sending and receiving zero or more messages.

You can read agent responses token-by-token as shown above regardless of whether the agent is streaming token by token or returning full messages. The complete message text will just be returned as a single "token" in the latter case.

## 📦 Pre-packaged agents (`miniagents.ext`)

⚠️ **ATTENTION!** Make sure to set your Anthropic API key in the `ANTHROPIC_API_KEY` environment variable before running the example below. ⚠️

```python
from miniagents import MiniAgents
from miniagents.ext import dialog_loop, markdown_history_agent
from miniagents.ext.llm import SystemMessage
from miniagents.ext.llm.anthropic import anthropic_agent

async def main() -> None:
    await dialog_loop.fork(
        assistant_agent=anthropic_agent.fork(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
        ),
        history_agent=markdown_history_agent,
    ).inquire(
        SystemMessage(
            "Your job is to improve the styling and grammar of the sentences that the user throws at you. Leave the sentences unchanged if they seem fine."
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

ANTHROPIC_AGENT: Hello! The greeting "hi" is a casual and commonly used informal salutation. It's grammatically correct and doesn't require any changes. If you'd like to provide a more formal or elaborate greeting, you could consider alternatives such as "Hello," "Good morning/afternoon/evening," or "Greetings."

USER: got it, thanks!

ANTHROPIC_AGENT: You're welcome! The phrase "Got it, thanks!" is a concise and informal way to express understanding and appreciation. It's perfectly fine as is for casual communication. If you wanted a slightly more formal version, you could say:

"I understand. Thank you!"

USER:
```

### 🔄 Implementing a custom dialog loop

Here is how you can implement a dialog loop between an agent and a user from the ground up yourself (for simplicity there is no history agent in this example - check out `in_memory_history_agent` and how it is used if you want to know how to implement your own history agent too):

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

The `AWAIT` sentinel is used to indicate that the loop should wait for the user input before proceeding to the next agent.

### 🌀 Agent parallelism explained

```python
from miniagents.miniagents import (
    MiniAgents,
    miniagent,
    InteractionContext,
    Message,
)

@miniagent
async def agent1(ctx: InteractionContext) -> None:
    print("Agent 1 started")
    ctx.reply("*** MESSAGE from Agent 1 ***")
    print("Agent 1 finished")

@miniagent
async def agent2(ctx: InteractionContext) -> None:
    print("Agent 2 started")
    ctx.reply("*** MESSAGE from Agent 2 ***")
    print("Agent 2 finished")

@miniagent
async def aggregator_agent(ctx: InteractionContext) -> None:
    print("Aggregator started")
    ctx.reply(
        [
            agent1.inquire(),
            agent2.inquire(),
            "*** MESSAGE #1 from Aggregator ***",
        ]
    )
    print("Aggregator still working")
    ctx.reply("*** MESSAGE #2 from Aggregator ***")
    print("Aggregator finished")

async def main() -> None:
    msg_promises = aggregator_agent.inquire()

    print("PREPARING TO DELIVER MESSAGES FROM AGGREGATOR")

    async for msg_promise in msg_promises:
        message: Message = await msg_promise
        print(message)
    print("TOTAL NUMBER OF MESSAGES FROM AGGREGATOR:", len(await msg_promises))

if __name__ == "__main__":
    MiniAgents().run(main())
```

This script will print the following lines to the console:

```
PREPARING TO DELIVER MESSAGES FROM AGGREGATOR
Aggregator started
Aggregator still working
Aggregator finished
Agent 1 started
Agent 1 finished
Agent 2 started
Agent 2 finished
*** MESSAGE from Agent 1 ***
*** MESSAGE from Agent 2 ***
*** MESSAGE #1 from Aggregator ***
*** MESSAGE #2 from Aggregator ***
TOTAL NUMBER OF MESSAGES FROM AGGREGATOR: 4
```

This specific order of print statements is due to the way asynchronous agents are designed in this framework. Notice that you don't see any `await` or `yield` statements in any of the agent functions above. Agent functions are defined as `async`, so you could have `await` statements inside of them for various reasons if you needed to. The agents from the example above just don't need that.

None of the agent functions start executing upon any of the calls to the `inquire()` method. Instead, in all cases, the `inquire()` method immediately returns with **promises** to "talk to the agents" (**promises** of sequences of **promises** of response messages, to be super precise - see `MessageSequencePromise` and `MessagePromise` classes for details).

As long as the global `start_asap` setting is set to `True` (which is the default - see the source code of `Promising`, the parent class of `MiniAgents` context manager for details), the actual agent functions will start processing at the earliest task switch (the behavior of `asyncio.create_task()`, which is used under the hood). In this example, it is going to be at the beginning of the first iteration of the `async for` loop inside the `main` function.

Keep in mind that this is not specifically because the aforementioned loop is trying to consume the responses that should come from those agents. If there was some other, unrelated task switch before any attempt to consume the responses (let's say `await asyncio.sleep(1)` some time before the loop), the processing of the agent functions would still have started, but now upon this other, unrelated task switch.

⚠️ **ATTENTION!** You can play around with setting `start_asap` to `False` for individual agent calls if for some reason you need to: `some_agent.inquire(request_messages_if_any, start_asap=False)`. However, setting it to `False` for the whole system globally is not recommended because it can lead to deadlocks. ⚠️

### 🧩 Existing Message models

```python
from miniagents.ext.llm import UserMessage, SystemMessage, AssistantMessage

user_message = UserMessage(text="Hello!")
system_message = SystemMessage(text="System message")
assistant_message = AssistantMessage(text="Assistant message")
```

The difference between these message types is in the default values of the `role` field of the message.

### 🛠️ Custom Message models

You can create custom message types by subclassing `Message`.

```python
from miniagents.messages import Message

class CustomMessage(Message):
    custom_field: str

message = CustomMessage(text="Hello", custom_field="Custom Value")
print(message.text)  # Output: Hello
print(message.custom_field)  # Output: Custom Value
```

## 🎯 Motivation behind this project?

There are three main features of MiniAgents that motivated the creation of this framework:

1. It is built around supporting asynchronous token streaming across chains of interconnected agents, making this the core feature of the framework.
2. It is very easy to throw bare strings, messages, message promises, collections, and sequences of messages and message promises (as well as the promises of the sequences themselves) all together into an agent reply (see `MessageType`). This entire hierarchical structure will be asynchronously resolved in the background into a flat and uniform sequence of message promises (it will be automatically "flattened" in the background).
3. By default, agents work in so-called `start_asap` mode, which is different from the usual way coroutines work where you need to actively await on them and/or iterate over them (in the case of asynchronous generators). In `start_asap` mode, every agent, after it was invoked, actively seeks every opportunity to proceed with its processing in the background when async tasks switch.

The third feature combines this `start_asap` approach with regular async/await and async generators by using so-called streamed promises (see `StreamedPromise` and `Promise` classes) which were designed to be "replayable" by nature.

It was chosen for messages to be immutable once they are created (see `Message` and `Frozen` classes) in order to make all of the above possible (because this way there are no concerns about the state of the message being changed in the background).

The `@MiniAgents().on_persist_message` decorator allows persisting messages as they are sent/received. Messages (as well as any other Pydantic models derived from `Frozen`) have a `hash_key` property that calculates the sha256 of the content of the message and is used as the id of the `Messages` (or any other `Frozen` model) much like there are commit hashes in git.

## 🌟 Some other features

- Hooks to persist messages as they are sent/received
- Typing with Pydantic for validation and serialization of messages

## 📚 Documentation

### 📂 Modules

The overall structure/hierarchy of the framework modules is as follows:

- `miniagents`: Core classes and functions.
- `miniagents.ext`: Pre-packaged agents and utilities.
- `miniagents.ext.llm`: Integrations with LLMs like OpenAI and Anthropic.
- `miniagents.promising`: Classes and functions related to promises and streaming.

### 🧠 Core Concepts

- **Agents**: Functions decorated with `@miniagent` that can send and receive messages.
- **Messages**: Immutable objects that are sent between agents.
- **Promises**: Objects representing future values or streams of values.
- **Streaming**: Asynchronous token and message streaming between agents.

## 📜 License

MiniAgents is released under the [MIT License](LICENSE).

## ❓ FAQ

**TODO** generate FAQ section

## 📝 Some notes for contributors

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders, and other components should always catch BaseExceptions and not just Exceptions**. This is because many of these components involve communications between async tasks via asyncio.Queue objects. Interrupting these promises with KeyboardInterrupt (which extends from BaseException) instead of letting it go through the queue can lead to hanging promises (a queue waiting for END_OF_QUEUE sentinel forever while the task that should send it is dead).

---

Happy coding with MiniAgents! 🚀
