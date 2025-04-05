<h1 align="center">🛰 MiniAgents 🌘</h1>

<p align="center">
    <a href="https://discord.gg/ptSvVnbwKt">
        <img alt="Discord"
            src="https://img.shields.io/discord/1356683647926796398?logo=discord&color=darkviolet">
    </a>
    <a href="https://github.com/teremterem/MiniAgents/blob/main/LICENSE">
        <img alt="License: MIT"
            src="https://img.shields.io/badge/license-MIT-blue">
    </a>
    <a href="https://www.python.org/downloads/">
        <img alt="Python: 3.9+"
            src="https://img.shields.io/badge/python-3.9+-olive">
    </a>
    <a href="https://pypi.org/project/miniagents/">
        <img alt="PyPI: Latest"
            src="https://img.shields.io/pypi/v/miniagents?color=mediumseagreen">
    </a>
    <a href="https://github.com/pylint-dev/pylint">
        <img alt="Linting: Pylint"
            src="https://img.shields.io/badge/linting-pylint-lightgray">
    </a>
    <a href="https://github.com/psf/black">
        <img alt="Code Style: Black"
            src="https://img.shields.io/badge/code%20style-black-black">
    </a>
</p>

<p align="center">
    <img alt="MiniAgents on the Moon"
        src="https://github.com/teremterem/MiniAgents/raw/main/images/miniagents-5-by-4-fixed.jpeg">
</p>

MiniAgents is an open-source Python framework that takes the complexity out of building multi-agent AI systems. With its innovative approach to parallelism and async-first design, you can focus on creating intelligent agents in an easy to follow procedural fashion while the framework handles the concurrency challenges for you.

Built on top of asyncio, MiniAgents provides a robust foundation for LLM-based applications with immutable, Pydantic-based messages and seamless asynchronous token and message streaming between agents.

## 💾 Installation

```bash
pip install -U miniagents
```

## ⚠️ IMPORTANT: START HERE FIRST! ⚠️

**We STRONGLY RECOMMEND checking this tutorial before you proceed with the README:**

### [📚 Building a Web Research Multi-Agent System](https://app.readytensor.ai/publications/miniagents-multi-agent-ai-with-procedural-simplicity-sZ9xgmyLOTyp)

The above step-by-step tutorial teaches you how to build a practical multi-agent web research system that can break down complex questions, run parallel searches, and synthesize comprehensive answers.

*Following that tutorial first will make the rest of this README easier to understand!*

---

## 🚀 Basic usage

Here's a simple example of how to define an agent:

```python
from miniagents import miniagent, InteractionContext, MiniAgents


@miniagent
async def my_agent(ctx: InteractionContext) -> None:
    async for msg_promise in ctx.message_promises:
        ctx.reply(f"You said: {await msg_promise}")


async def main() -> None:
    async for msg_promise in my_agent.trigger(["Hello", "World"]):
        print(await msg_promise)


if __name__ == "__main__":
    MiniAgents().run(main())
```

This script will print the following lines to the console:

```
You said: Hello
You said: World
```

### 🧨 Exception handling

Despite agents running in completely detached asyncio tasks, MiniAgents ensures proper exception propagation from callee agents to caller agents. When an exception occurs in a callee agent, it's captured and propagated through the promises of response message sequences. These exceptions are re-raised when those sequences are iterated over or awaited in any of the caller agents, ensuring that errors are not silently swallowed and can be properly handled.

Here's a simple example showing exception propagation:

```python
from miniagents import miniagent, InteractionContext, MiniAgents

@miniagent
async def faulty_agent(ctx: InteractionContext) -> None:
    # This agent will raise an exception
    raise ValueError("Something went wrong in callee agent")

@miniagent
async def caller_agent(ctx: InteractionContext) -> None:
    # The exception from faulty_agent WILL NOT propagate here
    faulty_response_promises = faulty_agent.trigger("Hello")
    try:
        # The exception from faulty_agent WILL propagate here
        async for msg_promise in faulty_response_promises:
            await msg_promise
    except ValueError as e:
        ctx.reply(f"Exception while iterating over response: {e}")

async def main() -> None:
    async for msg_promise in caller_agent.trigger("Start"):
        print(await msg_promise)

if __name__ == "__main__":
    MiniAgents().run(main())
```

Output:
```
Exception while iterating over response: Something went wrong in callee agent
```

### 🧠 Work with LLMs

MiniAgents provides built-in support for OpenAI and Anthropic language models with possibility to add other integrations.

⚠️ **ATTENTION!** Make sure to run `pip install -U openai` and set your OpenAI API key in the `OPENAI_API_KEY` environment variable before running the example below. ⚠️

```python
from miniagents import MiniAgents
from miniagents.ext.llms import OpenAIAgent

# NOTE: "Forking" an agent is a convenient way of creating a new agent instance
# with the specified configuration. Alternatively, you could pass the `model`
# parameter to `OpenAIAgent.trigger()` directly everytime you talk to the
# agent.
gpt_4o_agent = OpenAIAgent.fork(model="gpt-4o-mini")


async def main() -> None:
    reply_sequence = gpt_4o_agent.trigger(
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

Even though OpenAI models return a single assistant response, the `OpenAIAgent.trigger()` method is still designed to return a sequence of multiple message promises. This generalizes to arbitrary agents, making agents in the MiniAgents framework easily interchangeable (agents in this framework support sending and receiving zero or more messages).

You can read agent responses token-by-token as shown above regardless of whether the agent is streaming token by token or returning full messages. The complete message content will just be returned as a single "token" in the latter case.

## 🔄 A dialog loop between a user and an AI assistant

The `dialog_loop` agent is a pre-packaged agent that implements a dialog loop between a user agent and an assistant agent. Here is how you can use it to set up an interaction between a user and your agent (can be bare LLM agent, like `OpenAIAgent` or `AnthropicAgent`, can also be a custom agent that you define yourself - a more complex agent that uses LLM agents under the hood but also introduces more complex behavior, i.e. Retrieval Augmented Generation etc.):

⚠️ **ATTENTION!** Make sure to run `pip install -U openai` and set your OpenAI API key in the `OPENAI_API_KEY` environment variable before running the example below. ⚠️

```python
from miniagents import MiniAgents
from miniagents.ext import (
    dialog_loop,
    console_user_agent,
    MarkdownHistoryAgent,
)
from miniagents.ext.llms import SystemMessage, OpenAIAgent


async def main() -> None:
    dialog_loop.trigger(
        SystemMessage(
            "Your job is to improve the styling and grammar of the sentences "
            "that the user throws at you. Leave the sentences unchanged if "
            "they seem fine."
        ),
        user_agent=console_user_agent.fork(
            # Write chat history to a markdown file (`CHAT.md` in the current
            # working directory by default, fork `MarkdownHistoryAgent` if
            # you want to customize the filepath to write to).
            history_agent=MarkdownHistoryAgent
        ),
        assistant_agent=OpenAIAgent.fork(
            model="gpt-4o-mini",
            max_tokens=1000,
        ),
    )


if __name__ == "__main__":
    MiniAgents(
        # Log LLM prompts and responses to `llm_logs/` folder in the current
        # working directory. These logs will have a form of time-stamped
        # markdown files - single file per single prompt-response pair.
        llm_logger_agent=True
    ).run(main())
```

Here is what the interaction might look like if you run this script:

```
YOU ARE NOW IN A CHAT WITH AN AI ASSISTANT

Press Enter to send your message.
Press Ctrl+Space to insert a newline.
Press Ctrl+C (or type "exit") to quit the conversation.

USER: hi

OPENAI_AGENT: Hello! The greeting "hi" is casual and perfectly acceptable.
It's grammatically correct and doesn't require any changes. If you wanted
to use a more formal greeting, you could consider "Hello," "Good morning/afternoon/evening,"
or "Greetings."

USER: got it, thanks!

OPENAI_AGENT: You're welcome! "Got it, thanks!" is a concise and clear expression
of understanding and gratitude. It's perfectly fine for casual communication.
A slightly more formal alternative could be "I understand. Thank you!"
```

### 🧸 A "toy" implementation of a dialog loop

Here is how you can implement a dialog loop between an agent and a user from ground up yourself (for simplicity there is no history agent in this example - check out `in_memory_history_agent` and how it is used if you want to know how to implement your own history agent too):

```python
from miniagents import miniagent, InteractionContext, MiniAgents
from miniagents.ext import agent_loop, AWAIT


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
    agent_loop.trigger(agents=[user_agent, AWAIT, assistant_agent])


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

***Remember, with this framework the agents pass promises of message sequences between each other, not the already-resolved message sequences themselves! Even when you pass concrete messages in your code, they are still wrapped into promises of message sequences behind the scenes (while your async agent code is just sent to be processed in the background).***

For this reason, the presence of `AWAIT` sentinel in the agent chain in the example above is important. Without it the `agent_loop` would have kept scheduling more and more interactions between the agents of the chain without ever taking a break to catch up with their processing.

`AWAIT` forces the `agent_loop` to stop and `await` for the complete sequence of replies from the agent right before `AWAIT` prior to scheduling (triggering) the execution of the agent right after `AWAIT`, thus allowing it to catch up with the asynchronous processing of agents and their responses in the background.

### 📦 Some of the pre-packaged agents

- `miniagents.ext.llms`
  - `OpenAIAgent`: Connects to OpenAI models like GPT-4o, GPT-4o-mini, etc. Supports all OpenAI API parameters and handles token streaming seamlessly.
  - `AnthropicAgent`: Similar to OpenAIAgent but for Anthropic's Claude models.
- `miniagents.ext`
  - `console_input_agent`: Prompts the user for input via the console with support for multi-line input.
  - `console_output_agent`: Echoes messages to the console token by token, which is useful when the response is streamed from an LLM (if response messages are delivered all at once instead, this agent will also just print them all at once).
  - `file_output_agent`: Writes messages to a specified file, useful for saving responses from other agents.
  - `user_agent`: A user agent that echoes messages from the agent that called it, then reads the user input and returns the user input as its response. This agent is an aggregation of the `console_output_agent` and `console_input_agent` (these two agents can be substituted with other agents of similar functionality, however).
  - `agent_loop`: Creates an infinite loop of interactions between the specified agents. It's designed for ongoing conversations or continuous processing, particularly useful for chat interfaces where agents need to take turns indefinitely (or unless stopped with `KeyboardInterrupt`).
  - `dialog_loop`: A special case of `agent_loop` designed for conversation between a user and an assistant, with optional chat history tracking.
  - `agent_chain`: Executes a sequence of agents in order, where each agent processes the output of the previous agent. This creates a pipeline of processing steps, with messages flowing from one agent to the next in a specified sequence.
  - `in_memory_history_agent`: Keeps track of conversation history in memory, enabling context-aware interactions without external storage.
  - `MarkdownHistoryAgent`: Keeps track of conversation history in a markdown file, allowing to resume a conversation from the same point even if the app is restarted.
  - `markdown_llm_logger_agent`: Logs LLM interactions (prompts and responses) in markdown format, useful for debugging and auditing purposes (look for `llm_logger_agent=True` of the `MiniAgents()` context manager in one of the code examples above).

***Feel free to explore the source code in the `miniagents.ext` package to see how various agents are implemented and get inspiration for building your own!***

### 🔀 Agent parallelism explained

Let's consider an example that consists of two dummy agents and an aggregator agent that aggregates the responses from the two dummy agents (and also adds some messages of its own):

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
            agent1.trigger(),
            agent2.trigger(),
        ]
    )
    print("Aggregator still working")
    ctx.reply("*** AGGREGATOR MESSAGE #2 ***")
    print("Aggregator finished")


async def main() -> None:
    print("TRIGGERING AGGREGATOR")
    msg_promises = aggregator_agent.trigger()
    print("TRIGGERING AGGREGATOR DONE\n")

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
TRIGGERING AGGREGATOR
TRIGGERING AGGREGATOR DONE

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

None of the agent functions start executing upon any of the calls to the `trigger()` method. Instead, in all cases the `trigger()` method immediately returns with **promises** to "talk to the agent(s)" (**promises** of sequences of **promises** of response messages, to be very precise - see `MessageSequencePromise` and `MessagePromise` classes for details).

As long as the global `start_soon` setting is set to `True` (which is the default - see the source code of `PromisingContext`, the parent class of `MiniAgents` context manager for details), the actual agent functions will start processing at the earliest task switch (the behaviour of `asyncio.create_task()`, which is used under the hood). In this example it is going to be `await asyncio.sleep(1)` inside the `main()` function, but if this `sleep()` wasn't there, it would have happened upon the first iteration of the `async for` loop which is the next place where a task switch happens.

**💪 EXERCISE FOR READER:** Add another `await asyncio.sleep(1)` right before `print("Aggregator finished")` in the `aggregator_agent` function and then try to predict how the output will change. After that, run the modified script and check if your prediction was correct.

⚠️ **ATTENTION!** You can set `start_soon` to `False` for individual agent calls if you need to prevent them from starting any earlier than the first time their response sequence promise is awaited for: `some_agent.trigger(request_messages_if_any, start_soon=False)`. However, setting it to `False` for the whole system globally is not recommended because it can lead to deadlocks. ⚠️

### 📨 An alternative way to trigger agents

Here's a simple example demonstrating how to use `agent_call = some_agent.initiate_call()` and then do `agent_call.send_message()` two times before calling `agent_call.reply_sequence()` (instead of all-in-one `some_agent.trigger()`):

```python
from miniagents import miniagent, InteractionContext, MiniAgents


@miniagent
async def output_agent(ctx: InteractionContext) -> None:
    async for msg_promise in ctx.message_promises:
        ctx.reply(f"Echo: {await msg_promise}")


async def main() -> None:
    agent_call = output_agent.initiate_call()
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

1. Calling its `run()` method with your main function as a parameter (the `main()` function in this example should be defined as `async`):
   ```python
   MiniAgents().run(main())
   ```

2. Using it as an async context manager:
   ```python
   async with MiniAgents():
       ...  # your async code that works with agents goes here
   ```

3. Directly calling its `activate()` (and, potentially, `afinalize()` at the end) methods:
   ```python
   mini_agents = MiniAgents()
   mini_agents.activate()
   try:
       ...  # your async code that works with agents goes here
   finally:
       await mini_agents.afinalize()
   ```

The third way might be ideal for web applications and other cases when there is no single function that you can encapsulate with the `MiniAgents()` context manager (or it is unclear what such function would be). You just do `mini_agents.activate()` somewhere upon the init of the server and forget about it.

### 💬 Existing `Message` models

```python
from miniagents.ext.llms import UserMessage, SystemMessage, AssistantMessage

user_message = UserMessage("Hello!")
system_message = SystemMessage("System message")
assistant_message = AssistantMessage("Assistant message")
```

The difference between these message types is in the default values of the `role` field of the message:

- `UserMessage` has `role="user"` by default
- `SystemMessage` has `role="system"` by default
- `AssistantMessage` has `role="assistant"` by default

### 💭 Custom `Message` models

You can create custom message types by subclassing `Message`.

```python
from miniagents.messages import Message


class CustomMessage(Message):
    custom_field: str


message = CustomMessage("Hello", custom_field="Custom Value")
print(message.content)  # Output: Hello
print(message.custom_field)  # Output: Custom Value
```

---

For some more examples, check out the [examples](examples) directory.

## 💡 Motivation behind this project

There are two main features of MiniAgents the idea of which motivated the creation of this framework:

1. It is very easy to throw bare strings, messages, message promises, collections, and sequences of messages and message promises (as well as the promises of the sequences themselves) all together into an agent reply (see `MessageType`). This entire hierarchical structure will be asynchronously resolved in the background into a flat and uniform sequence of message promises (it will be automatically "flattened" in the background).
2. By default, agents work in so called `start_soon` mode, which is different from the usual way coroutines work where you need to actively await on them or iterate over them (in case of asynchronous generators). In `start_soon` mode, every agent, after it was invoked, actively seeks every opportunity to proceed its processing in the background when async tasks switch.

The second feature combines this `start_soon` approach with regular async/await and async generators by using so called streamed promises (see `StreamedPromise` and `Promise` classes) which were designed to be "replayable".

The design choice for immutable messages was made specifically to enable this kind of highly parallelized agent execution. Since Generative AI applications are inherently IO-bound (with models typically hosted externally), immutable messages eliminate concerns about concurrent state mutations. This approach allows multiple agents to process messages simultaneously without risk of race conditions or data corruption, maximizing throughput in distributed LLM workflows.

## 🔒 Message persistence and identification

MiniAgents provides a way to persist messages as they are resolved from promises using the `@MiniAgents().on_persist_message` decorator. This allows you to implement custom logic for storing or logging messages.

Additionally, messages (as well as any other Pydantic models derived from `Frozen`) have a `hash_key` property. This property calculates the sha256 hash of the content of the message and is used as the id of the `Messages` (or any other `Frozen` model), much like there are commit hashes in git.

Here's a simple example of how to use the `on_persist_message` decorator:

```python
from miniagents import MiniAgents, Message

mini_agents = MiniAgents()


@mini_agents.on_persist_message
async def persist_message(_, message: Message) -> None:
    print(f"Persisting message with hash key: {message.hash_key}")
    # Here you could save the message to a database or log it to a file
```

## 📚 Core concepts

Here are some of the core concepts in the MiniAgents framework:

- `MiniAgent`: A wrapper around an async function (or a whole class with `async def __call__()` method) that defines an agent's behavior. Created using the `@miniagent` decorator.
- `InteractionContext`: Passed to each agent function, provides access to incoming messages and allows sending replies.
- `Message`: Represents a message exchanged between agents. Can contain content, metadata, and nested messages. Immutable once created.
- `MessagePromise`: A promise of a message that can be streamed token by token.
- `MessageSequencePromise`: A promise of a sequence of message promises.
- `Frozen`: An immutable Pydantic model with a git-style hash key calculated from its JSON representation. The base class for `Message`.

More underlying concepts (you will rarely need to use them directly, if at all):

- `StreamedPromise`: A promise that can be resolved piece by piece, allowing for streaming. The base class for `MessagePromise` and `MessageSequencePromise`.
- `Promise`: Represents a value that may not be available yet, but will be resolved in the future. The base class for `StreamedPromise`.

## 👥 Community

Join our [Discord community](https://discord.gg/ptSvVnbwKt) to get help with your projects. We welcome questions, feature suggestions, and contributions!

## 📜 License

MiniAgents is released under the [MIT License](LICENSE).

---

Happy coding with MiniAgents! 🚀
