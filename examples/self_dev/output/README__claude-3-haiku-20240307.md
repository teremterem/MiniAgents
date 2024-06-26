# 🚀 MiniAgents

An asynchronous framework for building LLM-based multi-agent systems in Python, with a focus on immutable messages and token streaming.

## 💾 Installation

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
    ctx.reply([agent1.inquire(), agent2.inquire()])  # caveat: don't use generators here (TODO explain why)
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

**TODO** explain in detail the reason behind this specific order in which print statements printed their outputs in the
example above

**TODO** show an very simple example where you do `miniagent.start_inquiry()` and then do `.send_message()` two times
and then call `.reply_sequence()` (instead of all-in-one `miniagents.inquire()`)

**TODO** mention that you can `await` the whole `MessageSequencePromise`, resolving it into a tuple of `Message` objects
this way (give a very simple example)

**TODO** mention three ways MiniAgents() context can be used: calling its `run()` method with your main function as a
parameter, using it as an async context manager or directly calling its `activate()` (and, potentially, `afinalize()` at
the end) methods

### 🤖 Work with LLMs

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
        # MINOR: Let's separate messages with a double newline (even though in this particular case we are actually
        # going to receive only one message).
        print("\n\n")


if __name__ == "__main__":
    MiniAgents().run(main())
```

**TODO** explain that even though OpenAI models return a single assistant response, the `openai_agent.inquire()` method
is designed to return a sequence of messages (which is a sequence of message promises) that can be streamed token by
token to generalize to arbitrary agents making agents in the MiniAgents framework easily interchangeable (agents in this
framework support sending and receiving zero or more messages)

**TODO** mention that you can read agent responses token-by-token as shown above regardless of whether the agent is
streaming token by token or returning full messages (the complete message text will just be returned as a single "token"
in the latter case)

## 🧩 Some other pre-packaged agents (`miniagents.ext`)

**TODO** add a note about not forgetting to set the Anthropic API key

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

**TODO** explain the `dialog_loop` agent and the `markdown_history_agent` agents, also mention other agents
like `console_echo_agent`, `console_prompt_agent`, `user_agent` and `in_memory_history_agent`
**TODO** encourage the reader to explore the source code in `miniagents.ext` package on their own to see how various
agents are implemented

### 🧑‍💻 Here is how you can implement a dialog loop yourself from ground up

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
    # turn a sequence of message promises into a single message promise (if there had been multiple messages in the
    # sequence they would have had been separated by double newlines - this is how `as_single_promise()` by default)
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

**TODO** explain why AWAIT is used in the example above

### 🔧 Custom Message models

You can create custom message types by subclassing `Message`.

```python
from miniagents.messages import Message


class CustomMessage(Message):
    custom_field: str


message = CustomMessage(text="Hello", custom_field="Custom Value")
print(message.text)  # Output: Hello
print(message.custom_field)  # Output: Custom Value
```

### 📦 Existing Message models

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

**TODO** mention `@MiniAgents().on_persist_message` decorator that allows to persist messages as they are sent/received
and the fact that messages (as well as any other Pydantic models derived from `Frozen`) have `hash_key` property that
calculates the sha256 of the content of the message and is used as the id of the `Messages` (or any other `Frozen`
model) much like there are commit hashes in git.

## 🔍 Some other features

- Define agents as simple Python functions decorated with `@miniagent`
- Integrate with OpenAI and Anthropic LLMs using `openai_agent` and `anthropic_agent`
- Built on top of the `Promising` library (which is a library built directly inside this library 🙂) for managing
  asynchronous operations
- Asynchronous promise-based programming model with `Promise` and `StreamedPromise`
- Hooks to persist messages as they are sent/received
- Typing with Pydantic for validation and serialization of messages

## 📚 Documentation (TODO is this a good name for this section?)

### 🗂️ Modules

**TODO** describe the overall structure/hierarchy of the framework modules

### 🔑 Core Concepts

**TODO** explain core concepts

## 📄 License

MiniAgents is released under the [MIT License](../../../LICENSE).

## 🙋‍♂️ FAQ

**TODO** generate FAQ section (pull the questions out of your ass)

## 🤝 Some note(s) for contributors

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders and what not should always
  catch BaseExceptions and not just Exceptions** when they capture errors to pass those errors as "pieces" in order for
  those errors to be raised at the "consumer side". This is because many of the aforementioned Promising "primitives"
  are often part of mechanisms that involve communications between async tasks via asyncio.Queue objects and just
  interrupting those promises with KeyboardInterrupt which are extended from BaseException instead of letting
  KeyboardInterrupt to go through the queue leads to hanging of those promises (a queue is waiting for END_OF_QUEUE
  sentinel forever but the task that should send it is dead).

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders, and other components should always
  catch BaseExceptions and not just Exceptions**. This is because many of these components involve communications
  between async tasks via asyncio.Queue objects. Interrupting those promises with KeyboardInterrupt (which extends from
  BaseException) instead of letting it go through the queue can lead to hanging promises.

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders, and other components should always
  catch BaseExceptions and not just Exceptions**. This is because many of these components involve communications
  between async tasks via asyncio.Queue objects. Interrupting these promises with KeyboardInterrupt (which extends from
  BaseException) instead of letting it go through the queue can lead to hanging promises (a queue waiting for
  END_OF_QUEUE sentinel forever while the task that should send it is dead).

---

🚀 Happy coding with MiniAgents!
