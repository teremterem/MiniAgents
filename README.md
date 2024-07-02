<h1 align="center">🛰 MiniAgents 🌘</h1>

<p align="center">
    <a href="https://github.com/teremterem/MiniAgents/blob/main/LICENSE">
        <img alt="License: MIT"
            src="https://img.shields.io/badge/License-MIT-purple">
    </a>
    <a href="https://www.python.org/downloads/">
        <img alt="Python: 3.9+"
            src="https://img.shields.io/badge/python-3.9+-blue">
    </a>
    <a href="https://pypi.org/project/miniagents/">
        <img alt="PyPI: Latest"
            src="https://img.shields.io/pypi/v/miniagents?color=mediumseagreen">
    </a>
    <a href="https://github.com/pylint-dev/pylint">
        <img alt="Linting: Pylint"
            src="https://img.shields.io/badge/linting-pylint-olive">
    </a>
    <a href="https://github.com/psf/black">
        <img alt="Code Style: Black"
            src="https://img.shields.io/badge/code%20style-black-black">
    </a>
    <!-- TODO: CREATE DISCORD CHAT -->
</p>

<p align="center">
    <img alt="MiniAgents on the Moon"
        src="https://github.com/teremterem/MiniAgents/raw/main/images/miniagents-5-by-4-fixed.png">
</p>

A framework on top of asyncio for building LLM-based multi-agent systems in
Python, with immutable, Pydantic-based messages and a focus on asynchronous
token and message streaming between the agents.

## 💾 Installation

```bash
pip install -U miniagents
```

## 🚀 Usage

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

**TODO** show how (and when) to create class-based agents

### 🧠 Work with LLMs

MiniAgents provides built-in support for OpenAI and Anthropic language models
with possibility to add other integrations.

⚠️ **ATTENTION!** Make sure to run `pip install -U openai` and set your OpenAI
API key in the `OPENAI_API_KEY` environment variable before running the example
below. ⚠️

```python
from miniagents import MiniAgents
from miniagents.ext.llm import OpenAIAgent

# NOTE: "Forking" an agent is a convenient way of creating a new agent instance
# with the specified configuration. Alternatively, you could pass the `model`
# parameter to `OpenAIAgent.inquire()` directly everytime you talk to the
# agent.
gpt_4o_agent = OpenAIAgent.fork(model="gpt-4o-2024-05-13")


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
        # MINOR: Let's separate messages with a double newline (even though in
        # this particular case we are actually going to receive only one
        # message).
        print("\n")


if __name__ == "__main__":
    MiniAgents().run(main())
```

Even though OpenAI models return a single assistant response, the
`OpenAIAgent.inquire()` method is still designed to return a sequence of
multiple message promises. This generalizes to arbitrary agents, making agents
in the MiniAgents framework easily interchangeable (agents in this framework
support sending and receiving zero or more messages).

You can read agent responses token-by-token as shown above regardless of whether
the agent is streaming token by token or returning full messages. The complete
message text will just be returned as a single "token" in the latter case.

## 🔄 A dialog loop between a user and an AI assistant

The `dialog_loop` agent is a pre-packaged agent that implements a dialog loop
between a user agent and an assistant agent. Here is how you can use it to set
up an interaction between a user and your agent (can be bare LLM agent, like
`OpenAIAgent` or `AnthropicAgent`, can also be a custom agent that you define
yourself):

⚠️ **ATTENTION!** Make sure to run `pip install -U anthropic` and set your
Anthropic API key in the `ANTHROPIC_API_KEY` environment variable before running
the example below (or just replace `AnthropicAgent` with `OpenAIAgent` and
`"claude-3-5-sonnet-20240620"` with `"gpt-4o-2024-05-13"` if you already set up
the previous example). ⚠️

```python
from miniagents import MiniAgents
from miniagents.ext import (
    dialog_loop,
    console_user_agent,
    markdown_history_agent,
)
from miniagents.ext.llm import SystemMessage, AnthropicAgent


async def main() -> None:
    await dialog_loop.fork(
        user_agent=console_user_agent.fork(
            # Write chat history to a markdown file (`CHAT.md` in the current
            # working directory by default, fork `markdown_history_agent` if
            # you want to customize).
            history_agent=markdown_history_agent
        ),
        assistant_agent=AnthropicAgent.fork(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
        ),
    ).inquire(
        SystemMessage(
            "Your job is to improve the styling and grammar of the sentences "
            "that the user throws at you. Leave the sentences unchanged if "
            "they seem fine."
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

ANTHROPIC_AGENT: Hello! The greeting "hi" is a casual and commonly used informal
salutation. It's grammatically correct and doesn't require any changes. If you'd
like to provide a more formal or elaborate greeting, you could consider
alternatives such as "Hello," "Good morning/afternoon/evening," or "Greetings."

USER: got it, thanks!

ANTHROPIC_AGENT: You're welcome! The phrase "Got it, thanks!" is a concise and
informal way to express understanding and appreciation. It's perfectly fine as
is for casual communication. If you wanted a slightly more formal version, you
could say:

"I understand. Thank you!"
```

### 🧸 A "toy" implementation of a dialog loop

Here is how you can implement a dialog loop between an agent and a user from
ground up yourself (for simplicity there is no history agent in this example -
check out `in_memory_history_agent` and how it is used if you want to know how
to implement your own history agent too):

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
    # Turn a sequence of message promises into a single message promise (if
    # there had been multiple messages in the sequence they would have had
    # been separated by double newlines - this is how `as_single_promise()`
    # works by default).
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
```

**TODO** explain why the presence of `AWAIT` sentinel is important in the
example above

**TODO** or even better - show how to implement agent_loop from scratch

### 📦 Some other pre-packaged agents (`miniagents.ext`)

- `console_echo_agent`: Echoes messages to the console token by token.
- `console_prompt_agent`: Prompts the user for input via the console.
- `user_agent`: A user agent that echoes messages from the agent that called it,
  then reads the user input and returns the user input as its response. This
  agent is an aggregation of the previous two.
- `agent_loop`: **TODO** explain
- `agent_chain`: **TODO** explain

Feel free to explore the source code in the `miniagents.ext` package to see how
various agents are implemented and get inspiration for building your own agents!

### 🔀 Agent parallelism explained

Let's consider an example that consists of two dummy agents and an aggregator
agent that aggregates the responses from the two dummy agents (and also adds
some messages of its own):

```python
import asyncio
from miniagents.miniagents import (
    MiniAgents,
    miniagent,
    InteractionContext,
    Message,
)


@miniagent
async def agent1(ctx: InteractionContext) -> None:
    print("Agent 1 started")
    ctx.reply("*** MESSAGE #1 from Agent 1 ***")
    print("Agent 1 still working")
    ctx.reply("*** MESSAGE #2 from Agent 1 ***")
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
            "*** AGGREGATOR MESSAGE #1 ***",
            agent1.inquire(),
            agent2.inquire(),
        ]
    )
    print("Aggregator still working")
    ctx.reply("*** AGGREGATOR MESSAGE #2 ***")
    print("Aggregator finished")


async def main() -> None:
    print("INQUIRING ON AGGREGATOR")
    msg_promises = aggregator_agent.inquire()
    print("INQUIRING DONE\n")

    print("SLEEPING FOR ONE SECOND")
    # This is when the agents will actually start processing (in fact, any
    # other kind of task switch would have had the same effect).
    await asyncio.sleep(1)
    print("SLEEPING DONE\n")

    print("PREPARING TO GET MESSAGES FROM AGGREGATOR")
    async for msg_promise in msg_promises:
        # MessagePromises always resolve into Message objects (or subclasses),
        # even if the agent was replying with bare strings
        message: Message = await msg_promise
        print(message)

    # You can safely `await` again. Concrete messages (and tokens, if there was
    # token streaming) are cached inside the promises. Message sequences (as
    # well as token sequences) are "replayable".
    print("TOTAL NUMBER OF MESSAGES FROM AGGREGATOR:", len(await msg_promises))


if __name__ == "__main__":
    MiniAgents().run(main())
```

This script will print the following lines to the console:

```
INQUIRING ON AGGREGATOR
INQUIRING DONE

SLEEPING FOR ONE SECOND
Aggregator started
Aggregator still working
Aggregator finished
Agent 1 started
Agent 1 still working
Agent 1 finished
Agent 2 started
Agent 2 finished
SLEEPING DONE

PREPARING TO GET MESSAGES FROM AGGREGATOR
*** AGGREGATOR MESSAGE #1 ***
*** MESSAGE #1 from Agent 1 ***
*** MESSAGE #2 from Agent 1 ***
*** MESSAGE from Agent 2 ***
*** AGGREGATOR MESSAGE #2 ***
TOTAL NUMBER OF MESSAGES FROM AGGREGATOR: 5
```

None of the agent functions start executing upon any of the calls to the
`inquire()` method. Instead, in all cases the `inquire()` method immediately
returns with **promises** to "talk to the agent(s)" (**promises** of sequences
of **promises** of response messages, to be super precise - see
`MessageSequencePromise` and `MessagePromise` classes for details).

As long as the global `start_asap` setting is set to `True` (which is the
default - see the source code of `Promising`, the parent class of `MiniAgents`
context manager for details), the actual agent functions will start processing
at the earliest task switch (the behaviour of `asyncio.create_task()`, which is
used under the hood). In this example it is going to be `await asyncio.sleep(1)`
inside the `main()` function, but if this `sleep()` wasn't there, it would have
happened upon the first iteration of the `async for` loop which is the next
place where a task switch happens.

**💪 EXERCISE FOR READER:** Add another `await asyncio.sleep(1)` right before
`print("Aggregator finished")` in the `aggregator_agent` function and then try
to predict how the output will change. After that, run the modified script and
check if your prediction was correct.

⚠️ **ATTENTION!** You can play around with setting `start_asap` to `False` for
individual agent calls if for some reason you need to:
`some_agent.inquire(request_messages_if_any, start_asap=False)`. However,
setting it to `False` for the whole system globally is not recommended because
it can lead to deadlocks. ⚠️

### 📨 An alternative inquiry method

Here's a simple example demonstrating how to use
`agent_call = some_agent.initiate_inquiry()` and then do
`agent_call.send_message()` two times before calling
`agent_call.reply_sequence()` (instead of all-in-one `some_agent.inquire()`):

```python
from miniagents import miniagent, InteractionContext, MiniAgents


@miniagent
async def echo_agent(ctx: InteractionContext):
    async for msg_promise in ctx.message_promises:
        ctx.reply(f"Echo: {await msg_promise}")


async def main():
    agent_call = echo_agent.initiate_inquiry()
    agent_call.send_message("Hello")
    agent_call.send_message("World")
    reply_sequence = agent_call.reply_sequence()

    async for msg_promise in reply_sequence:
        print(await msg_promise)


if __name__ == "__main__":
    MiniAgents().run(main())
```

This will output:

```
Echo: Hello
Echo: World
```

### 🛠️ Global `MiniAgents()` context

There are three ways to use the `MiniAgents()` context:

1. Calling its `run()` method with your main function as a parameter (the
   `main()` function in this example should be defined as `async`):
   ```python
   MiniAgents().run(main())
   ```

2. Using it as an async context manager:
   ```python
   async with MiniAgents():
       ...  # your async code that works with agents goes here
   ```

3. Directly calling its `activate()` (and, potentially, `afinalize()` at the
   end) methods:
   ```python
   mini_agents = MiniAgents()
   mini_agents.activate()
   try:
       ...  # your async code that works with agents goes here
   finally:
       await mini_agents.afinalize()
   ```

The third way might be ideal for web applications and other cases when there is
no single function that you can encapsulate with the `MiniAgents()` context
manager (or it is unclear what such function would be). You just do
`mini_agents.activate()` somewhere upon the init of the server and forget
about it.

### 💬 Existing `Message` models

```python
from miniagents.ext.llm import UserMessage, SystemMessage, AssistantMessage

user_message = UserMessage(text="Hello!")
system_message = SystemMessage(text="System message")
assistant_message = AssistantMessage(text="Assistant message")
```

The difference between these message types is in the default values of
the `role` field of the message:

- `UserMessage` has `role="user"` by default
- `SystemMessage` has `role="system"` by default
- `AssistantMessage` has `role="assistant"` by default

### 💭 Custom `Message` models

You can create custom message types by subclassing `Message`.

```python
from miniagents.messages import Message


class CustomMessage(Message):
    custom_field: str


message = CustomMessage(text="Hello", custom_field="Custom Value")
print(message.text)  # Output: Hello
print(message.custom_field)  # Output: Custom Value
```

---

For more advanced usage, check out the [examples](examples) directory.

## 💡 Motivation behind this project

There are three main features of MiniAgents the idea of which motivated the
creation of this framework:

1. It is built around supporting asynchronous token streaming across chains of
   interconnected agents, making this the core feature of the framework.
2. It is very easy to throw bare strings, messages, message promises,
   collections, and sequences of messages and message promises (as well as the
   promises of the sequences themselves) all together into an agent reply (see
   `MessageType`). This entire hierarchical structure will be asynchronously
   resolved in the background into a flat and uniform sequence of message
   promises (it will be automatically "flattened" in the background).
3. By default, agents work in so called `start_asap` mode, which is different
   from the usual way coroutines work where you need to actively await on them
   and/or iterate over them (in case of asynchronous generators). In
   `start_asap` mode, every agent, after it was invoked, actively seeks every
   opportunity to proceed its processing in the background when async tasks
   switch.

The third feature combines this `start_asap` approach with regular async/await
and async generators by using so called streamed promises (see `StreamedPromise`
and `Promise` classes) which were designed to be "replayable" by nature.

It was chosen for messages to be immutable once they are created (see `Message`
and `Frozen` classes) in order to make all of the above possible (because this
way there are no concerns about the state of the message being changed in the
background).

## 🔒 Message persistence and identification

MiniAgents provides a way to persist messages as they are resolved from promises
using the `@MiniAgents().on_persist_message` decorator. This allows you to
implement custom logic for storing or logging messages.

Additionally, messages (as well as any other Pydantic models derived from
`Frozen`) have a `hash_key` property. This property calculates the sha256 hash
of the content of the message and is used as the id of the `Messages` (or any
other `Frozen` model), much like there are commit hashes in git.

Here's a simple example of how to use the `on_persist_message` decorator:

```python
from miniagents import MiniAgents, Message

mini_agents = MiniAgents()


@mini_agents.on_persist_message
async def persist_message(_, message: Message) -> None:
    print(f"Persisting message with hash key: {message.hash_key}")
    # Here you could implement logic to save the message to a database, for example
```

## 📂 Modules

Here's an overview of the module structure and hierarchy in the MiniAgents
framework:

- `miniagents`: The core package containing the main classes and functions
    - `miniagents.py`: Defines the `MiniAgents` context manager, `MiniAgent`
      class, and `miniagent` decorator
    - `messages.py`: Defines the `Message` class and related message types
    - `miniagent_typing.py`: Defines type aliases and protocols used in the
      framework
    - `utils.py`: Utility functions used throughout the framework
    - `promising`: Subpackage for the "promising" functionality (promises,
      streaming, etc.)
        - `promising.py`: Defines the `Promise` and `StreamedPromise` classes
        - `promise_typing.py`: Defines type aliases and protocols for promises
        - `sequence.py`: Defines the `FlatSequence` class for flattening
          sequences
        - `sentinels.py`: Defines sentinel objects used in the framework
        - `errors.py`: Defines custom exception classes
        - `ext`: Subpackage for extensions to the promising functionality
            - `frozen.py`: Defines the `Frozen` class for immutable Pydantic
              models
- `miniagents.ext`: Subpackage for pre-packaged agents and extensions
    - `agent_aggregators.py`: Agents for aggregating other agents (chains,
      loops, etc.)
    - `history_agents.py`: Agents for managing conversation history
    - `misc_agents.py`: Miscellaneous utility agents
    - `llm`: Subpackage for LLM integrations
        - `llm_common.py`: Common classes and functions for LLM agents
        - `openai.py`: OpenAI LLM agent
        - `anthropic.py`: Anthropic LLM agent

## 📚 Core concepts

Here are some of the core concepts in the MiniAgents framework:

- **MiniAgent**: A wrapper around an async function that defines an agent's
  behavior. Created using the `@miniagent` decorator.
- **InteractionContext**: Passed to each agent function, provides access to
  incoming messages and allows sending replies.
- **Message**: Represents a message exchanged between agents. Can contain text,
  metadata, and nested messages. Immutable once created.
- **MessagePromise**: A promise of a message that can be streamed token by
  token.
- **MessageSequencePromise**: A promise of a sequence of message promises.
- **Promise**: Represents a value that may not be available yet, but will be
  resolved in the future.
- **StreamedPromise**: A promise that can be resolved piece by piece, allowing
  for streaming.
- **Frozen**: An immutable Pydantic model with a git-style hash key calculated
  from its JSON representation.

## 📜 License

MiniAgents is released under the [MIT License](LICENSE).

## 📝 Note to contributors

- **Different Promise and StreamedPromise resolvers, piece-by-piece streamers,
  appenders, and other Promising components should always catch BaseExceptions
  and not just Exceptions**. This is because many of these components involve
  communications between async tasks via `asyncio.Queue` objects. Interrupting
  these promises with `KeyboardInterrupt` (which extends from `BaseException`)
  instead of letting it go through the queue can lead to hanging promises (a
  queue waiting for `END_OF_QUEUE` sentinel forever while the task that should
  send it is dead).

---

Happy coding with MiniAgents! 🚀
