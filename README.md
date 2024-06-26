# MiniAgents

A framework on top of asyncio for building LLM-based multi-agent systems in Python, with immutable, Pydantic-based
messages and a focus on asynchronous token and message streaming between agents.

## What was the motivation behind this project?

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

## Some other features

- Define agents as simple Python functions decorated with `@miniagent`
- Integrate with OpenAI and Anthropic LLMs using `openai_agent` and `anthropic_agent`
- Built on top of the `Promising` library (which is a library built directly inside this library 🙂) for managing
  asynchronous operations
- Asynchronous promise-based programming model with `Promise` and `StreamedPromise`
- Hooks to persist messages as they are sent/received
- Typing with Pydantic for validation and serialization of messages

## Installation

```bash
pip install miniagents
```

## Usage

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

### Slightly more advanced example

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

**TODO** explain in detail the reason behind this specific order in which print statements printed their outputs in the
example above

**TODO** show an very simple example where you do `miniagent.start_inquiry()` and then do `.send_message()` two times
and then call `.reply_sequence()` (instead of all-in-one `miniagents.inquire()`)

**TODO** mention that you can `await` the whole `MessageSequencePromise`, resolving it into a tuple of `Message` objects
this way (give a very simple example)

**TODO** mention three ways MiniAgents() context can be used: calling its `run()` method with your main function as a
parameter, using it as an async context manager or directly calling its `activate()` (and, potentially, `afinalize()` at
the end) methods

### Work with LLMs

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
        # MINOR: Let's separate messages with a double newline (even though in this particular case we are actually
        # going to receive only one message).
        print("\n")


if __name__ == "__main__":
    MiniAgents().run(amain())
```

**TODO** explain that even though OpenAI models return a single assistant response, the `openai_agent.inquire()` method
is designed to return a sequence of messages (which is a sequence of message promises) that can be streamed token by
token to generalize to arbitrary agents making agents in the MiniAgents framework easily interchangeable (agents in this
framework support sending and receiving zero or more messages)

**TODO** mention that you can read agent responses token-by-token as shown above regardless of whether the agent is
streaming token by token or returning full messages (the complete message text will just be returned as a single "token"
in the latter case)

## Some other pre-packaged agents (`miniagents.ext`)

**TODO** add a note about not forgetting to set the Anthropic API key

```python
from miniagents import MiniAgents
from miniagents.ext import dialog_loop, markdown_history_agent
from miniagents.ext.llm import SystemMessage
from miniagents.ext.llm.anthropic import anthropic_agent


async def amain() -> None:
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

**TODO** explain the `dialog_loop` agent and the `markdown_history_agent` agents, also mention other agents
like `console_echo_agent`, `console_prompt_agent`, `user_agent` and `in_memory_history_agent`
**TODO** encourage the reader to explore the source code in `miniagents.ext` package on their own to see how various
agents are implemented

### Here is how you can implement a dialog loop yourself from ground up

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

**TODO** explain why AWAIT is used in the example above

###### TODO TODO TODO TODO TODO ######

###### TODO TODO TODO TODO TODO ######

###### TODO TODO TODO TODO TODO ######

###### TODO TODO TODO TODO TODO ######

###### TODO TODO TODO TODO TODO ######

### Advanced Example with Multiple Agents

You can create more complex interactions involving multiple agents:

### Message Handling

MiniAgents provides a structured way to handle messages using the `Message` class and its derivatives.

You can create custom message types by subclassing `Message`.

```python
from miniagents.messages import Message


class CustomMessage(Message):
    custom_field: str


message = CustomMessage(text="Hello", custom_field="Custom Value")
print(message.text)  # Output: Hello
print(message.custom_field)  # Output: Custom Value
```

### Handling Messages

MiniAgents provides a structured way to handle messages. You can define different types of messages such
as `UserMessage`, `SystemMessage`, and `AssistantMessage`:

```python
from miniagents.ext.llm.llm_common import UserMessage, SystemMessage, AssistantMessage

user_message = UserMessage(text="Hello!")
system_message = SystemMessage(text="System message")
assistant_message = AssistantMessage(text="Assistant message")
```

**TODO** mention that exceptions in agents are treated as messages ?

For more advanced usage, check out the [examples](examples/) directory.

## Utility Functions

### Joining Messages

You can join multiple messages into a single message using the `join_messages` function:

```python
from miniagents.utils import join_messages


async def main():
    messages = ["Hello", "world"]
    joined_message = join_messages(messages)
    print(await joined_message.aresolve())


miniagents.run(main())
```

### Splitting Messages

You can split a message into multiple messages using the `split_messages` function:

```python
from miniagents.utils import split_messages


async def main():
    message = "Hello\n\nworld"
    split_message = split_messages(message)
    print(await split_message)


miniagents.run(main())
```

## Utilities

MiniAgents provides several utility functions to help with common tasks:

- **join_messages**: Join multiple messages into a single message.
- **split_messages**: Split a message into multiple messages based on a delimiter.

Example of joining messages:

```python
from miniagents.utils import join_messages


async def main():
    async with MiniAgents() as context:
        joined_message = join_messages(["Hello", "World"], delimiter=" ")
        print(await joined_message.aresolve())


MiniAgents().run(main())
```

## Documentation

### Modules

- `miniagents`: Core classes and functions.
- `miniagents.ext`: Extensions for integrating with external services and libraries.
- `miniagents.promising`: Classes and functions for handling promises and asynchronous operations.
- `miniagents.utils`: Utility functions for common tasks.

The framework is organized into several modules:

- `miniagents.miniagents`: Core classes for creating and managing agents
- `miniagents.messages`: Classes for representing and handling messages
- `miniagents.promising`: Utilities for managing asynchronous operations using promises
- `miniagents.ext`: Extensions for integrating with external services and utilities
    - `miniagents.ext.chat_history_md`: Chat history management using Markdown files
    - `miniagents.ext.console_user_agent`: User agent for interacting via the console
    - `miniagents.ext.llm`: Integration with language models
        - `miniagents.ext.llm.openai`: OpenAI language model integration
        - `miniagents.ext.llm.anthropic`: Anthropic language model integration

For detailed documentation on each module and class, please refer to the docstrings in the source code.

### Extending MiniAgents

You can extend the functionality of MiniAgents by creating custom agents, message types, and chat history handlers. The
framework is designed to be modular and flexible, allowing you to integrate it with various services and customize its
behavior to fit your needs.

### Core Concepts

#### MiniAgents

`MiniAgents` is the main context manager that handles the lifecycle of agents and promises.

```python
from miniagents import MiniAgents

async with MiniAgents():
# Your code here
```

#### MiniAgent

A `MiniAgent` is a wrapper for an agent function that allows calling the agent.

```python
from miniagents import miniagent


@miniagent
async def my_agent(ctx, **kwargs):
# Agent logic here
```

- `MiniAgents`: The main context manager for running agents
- **MiniAgents**: The main class that manages the lifecycle of agents and their interactions.
- `@miniagent`: Decorator for defining agents
- **MiniAgent**: A wrapper for an agent function that allows calling the agent.
- `MiniAgent` - A wrapper around a Python function that allows it to send and receive messages
- **InteractionContext**: Provides context for the interaction, including the messages and the agent.
- **Message**: Represents a message that can be sent between agents.
- `Message` - Represents a message that can be sent between agents, with optional metadata
- **MessagePromise**: A promise of a message that can be streamed token by token.
- **MessageSequencePromise**: A promise of a sequence of messages that can be streamed message by message.

- `openai_agent`: an OpenAI language model agent
- `anthropic_agent`: an Anthropic language model agent

### Core Classes

- `MiniAgents`: The main context manager for managing agents and their interactions.
- `MiniAgent`: A wrapper for an agent function that allows calling the agent.
- `InteractionContext`: Provides context for an agent's interaction, including the messages and reply streamer.
- `InteractionContext`: Passed to agent functions, provides methods for replying and finishing early

### Message Handling

- `Message`: Represents a message that can be sent between agents.
- `Message`: Represents a message passed between agents
- `MessagePromise`: A promise of a message that can be streamed token by token.
- `MessagePromise`: A promise that resolves to a message
- `MessageSequencePromise`: A promise of a sequence of messages that can be streamed message by message.
- `ChatHistory`: An abstract class for managing chat history.

### Promising

- `Promise`: Represents a promise of a value that will be resolved asynchronously.
- `StreamedPromise`: Represents a promise of a whole value that can be streamed piece by piece.
- `StreamAppender`: Allows appending pieces to a stream that is consumed by a `StreamedPromise`.

### Utilities

- `adialog_loop`: Run a dialog loop between a user agent and assistant agent
- `achain_loop`: Run a loop that chains multiple agents together
- `achain_loop`: Runs a loop of agents, chaining their interactions.
- `join_messages`: Joins multiple messages into a single message using a delimiter.
- `split_messages`: Splits messages based on a delimiter.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](LICENSE).

## FAQ

1. **Q: How does MiniAgents differ from other agent frameworks?**
   A: MiniAgents focuses on asynchronous execution, immutable message passing, and easy integration with LLMs. It's
   designed for building complex, streaming-capable multi-agent systems.

2. **Q: Can I use MiniAgents with LLM providers other than OpenAI and Anthropic?**
   A: Yes, the framework is extensible. You can create custom agents for other LLM providers by following the patterns
   in the existing implementations.

3. **Q: How does MiniAgents handle errors in agents?**
   A: Exceptions in agents are treated as messages, allowing for graceful error handling and recovery in multi-agent
   systems.

4. **Q: Is MiniAgents suitable for production use?**
   A: While MiniAgents is being actively developed, it's designed with production use cases in mind. However, always
   thoroughly test and evaluate it for your specific needs.

5. **Q: How can I persist agent interactions?**
   A: MiniAgents provides built-in support for chat history management, including in-memory and Markdown-based
   persistence options.

Q: How does MiniAgents handle errors in agents?
A: Exceptions in agents are treated as messages and can be caught and handled by other agents in the chain.

Q: Can I use MiniAgents with other LLM providers?
A: Yes, the framework is designed to be extensible. You can create custom agents for other LLM providers by following
the patterns used for OpenAI and Anthropic integrations.

Q: How does token streaming work in MiniAgents?
A: Token streaming is implemented using the `StreamedPromise` class, which allows for piece-by-piece consumption of LLM
outputs.

Q: Is MiniAgents suitable for production use?
A: While MiniAgents is actively developed and used in various projects, it's always recommended to thoroughly test and
evaluate the framework for your specific use case before deploying to production.

1. **Q: How does MiniAgents differ from other agent frameworks?**
   A: MiniAgents focuses on asynchronous communication, immutable messages, and seamless integration with LLMs. It
   provides a simple API for defining agents as Python functions while handling complex interactions behind the scenes.

2. **Q: Can I use MiniAgents with LLMs other than OpenAI and Anthropic?**
   A: Yes, the framework is designed to be extensible. You can create custom integrations for other LLM providers by
   following the patterns in the existing integrations.

3. **Q: How does token streaming work in MiniAgents?**
   A: MiniAgents uses `StreamedPromise` objects to handle token streaming. This allows for efficient processing of LLM
   responses as they are generated, rather than waiting for the entire response.

4. **Q: What are the benefits of using immutable messages?**
   A: Immutable messages ensure that the state of conversations remains consistent and predictable. This helps prevent
   bugs related to unexpected state changes and makes it easier to reason about the flow of information between agents.

5. **Q: How can I persist chat history in MiniAgents?**
   A: MiniAgents provides built-in support for in-memory chat history and Markdown-based persistence. You can also
   create custom chat history handlers by extending the `ChatHistory` class.

## Things to remember (for the developers of this framework)

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders and what not should always catch
  BaseExceptions and not just Exceptions** when they capture errors to pass those errors as "pieces" in order for
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

This README provides an overview of the MiniAgents framework, its features, installation instructions, usage examples,
and information on testing and contributing. For more detailed documentation, please refer to the source code and
comments within the project.

---

Happy coding with MiniAgents! 🚀
