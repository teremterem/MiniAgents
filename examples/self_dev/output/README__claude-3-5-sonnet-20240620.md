# 🚀 MiniAgents

A framework on top of asyncio for building LLM-based multi-agent systems in Python, with immutable, Pydantic-based messages and a focus on asynchronous token and message streaming between agents.

## 📥 Installation

```bash
pip install miniagents
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

The specific order of the print statements is due to the asynchronous nature of the agents and how they are scheduled. Here's a breakdown:

1. The main function starts and calls `aggregator_agent.inquire()`.
2. The aggregator agent starts and immediately finishes, scheduling `agent1` and `agent2` to run.
3. `agent1` and `agent2` are then executed concurrently.
4. The main function waits for and prints the messages from `agent1` and `agent2`.
5. The main function finishes.

Here's an example of using `miniagent.start_inquiry()` and `.send_message()`:

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

You can also `await` the whole `MessageSequencePromise`, resolving it into a tuple of `Message` objects:

```python
messages = await echo_agent.inquire(["Hello", "World"])
for message in messages:
    print(message.text)
```

There are three ways to use the `MiniAgents()` context:

1. Calling its `run()` method with your main function as a parameter:
   ```python
   MiniAgents().run(main())
   ```

2. Using it as an async context manager:
   ```python
   async with MiniAgents():
       await main()
   ```

3. Directly calling its `activate()` and `afinalize()` methods:
   ```python
   mini_agents = MiniAgents()
   mini_agents.activate()
   try:
       await main()
   finally:
       await mini_agents.afinalize()
   ```

### 🤖 Work with LLMs

MiniAgents provides built-in support for OpenAI and Anthropic language models (with the possibility to add other integrations).

**NOTE:** Make sure to set your OpenAI API key in the `OPENAI_API_KEY` environment variable before running the example below.

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

Even though OpenAI models return a single assistant response, the `openai_agent.inquire()` method is designed to return a sequence of messages (which is a sequence of message promises) that can be streamed token by token. This design generalizes to arbitrary agents, making agents in the MiniAgents framework easily interchangeable. Agents in this framework support sending and receiving zero or more messages.

You can read agent responses token-by-token as shown above, regardless of whether the agent is streaming token by token or returning full messages. In the latter case, the complete message text will be returned as a single "token".

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

The `dialog_loop` agent manages the back-and-forth conversation between the user and the assistant agent. It handles the flow of messages and ensures that each participant gets a turn to respond.

The `markdown_history_agent` is responsible for logging the conversation history to a markdown file. By default, it writes to a file named `CHAT.md` in the current working directory. You can customize this by forking the agent and specifying a different file path.

Other useful agents include:
- `console_echo_agent`: Echoes messages to the console.
- `console_prompt_agent`: Prompts the user for input via the console.
- `user_agent`: Represents the user in a conversation.
- `in_memory_history_agent`: Keeps the conversation history in memory.

Feel free to explore the source code in the `miniagents.ext` package to see how these various agents are implemented and to discover more agents that might be useful for your projects.

### 🛠️ Here is how you can implement a dialog loop yourself from ground up

For more advanced usage, you can define multiple agents and manage their interactions (for simplicity, there is no history agent in this particular example):

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

The `AWAIT` sentinel is used in the example above to ensure that the `user_agent` completes its execution before the `assistant_agent` starts. This creates a turn-based conversation flow where the user input is fully processed before the assistant responds.

### 📝 Custom Message models

You can create custom message types by subclassing `Message`:

```python
from miniagents.messages import Message

class CustomMessage(Message):
    custom_field: str

message = CustomMessage(text="Hello", custom_field="Custom Value")
print(message.text)  # Output: Hello
print(message.custom_field)  # Output: Custom Value
```

### 📚 Existing Message models

```python
from miniagents.ext.llm import UserMessage, SystemMessage, AssistantMessage

user_message = UserMessage(text="Hello!")
system_message = SystemMessage(text="System message")
assistant_message = AssistantMessage(text="Assistant message")
```

---

For more advanced usage, check out the [examples](examples/) directory.

## 💡 What was the motivation behind this project?

There are three main features of MiniAgents that motivated the creation of this framework:

1. It is built around supporting asynchronous token streaming across chains of interconnected agents, making this the core feature of the framework.
2. It is very easy to throw bare strings, messages, message promises, collections, and sequences of messages and message promises (as well as the promises of the sequences themselves) all together into an agent reply (see `MessageType`). This entire hierarchical structure will be asynchronously resolved in the background into a flat and uniform sequence of message promises (it will be automatically "flattened" in the background).
3. By default, agents work in so-called `start_asap` mode, which is different from the usual way coroutines work where you need to actively await on them and/or iterate over them (in case of asynchronous generators). In `start_asap` mode, every agent, after it was invoked, actively seeks every opportunity to proceed its processing in the background when async tasks switch.

The third feature combines this `start_asap` approach with regular async/await and async generators by using so-called streamed promises (see `StreamedPromise` and `Promise` classes) which were designed to be "replayable" by nature.

It was chosen for messages to be immutable once they are created (see `Message` and `Frozen` classes) in order to make all of the above possible (because this way there are no concerns about the state of the message being changed in the background).

You can use the `@MiniAgents().on_persist_message` decorator to persist messages as they are sent/received. Messages (as well as any other Pydantic models derived from `Frozen`) have a `hash_key` property that calculates the sha256 of the content of the message and is used as the id of the `Messages` (or any other `Frozen` model), much like there are commit hashes in git.

Example:

```python
from miniagents import MiniAgents, Message

mini_agents = MiniAgents()

@mini_agents.on_persist_message
async def persist_message(_, message: Message) -> None:
    print(f"Persisting message with hash key: {message.hash_key}")
    # Your persistence logic here

# ... rest of your code
```

## 🌟 Some other features

- Define agents as simple Python functions decorated with `@miniagent`
- Integrate with OpenAI and Anthropic LLMs using `openai_agent` and `anthropic_agent`
- Built on top of the `Promising` library (which is a library built directly inside this library 🙂) for managing asynchronous operations
- Asynchronous promise-based programming model with `Promise` and `StreamedPromise`
- Hooks to persist messages as they are sent/received
- Typing with Pydantic for validation and serialization of messages

## 📚 Framework Structure

### 🗂️ Modules

The MiniAgents framework is organized into several modules:

- `miniagents`: The core package containing the main functionality.
  - `miniagents.miniagents`: Core classes for defining and managing agents.
  - `miniagents.messages`: Message-related classes and utilities.
  - `miniagents.promising`: Asynchronous promise-based programming utilities.
  - `miniagents.ext`: Extensions and pre-packaged agents.
    - `miniagents.ext.llm`: Language model integrations (OpenAI, Anthropic).
    - `miniagents.ext.agent_aggregators`: Agents for chaining and aggregating other agents.
    - `miniagents.ext.history_agents`: Agents for managing conversation history.
    - `miniagents.ext.misc_agents`: Miscellaneous utility agents.

### 🧠 Core Concepts

1. **Agents**: Defined using the `@miniagent` decorator, these are the building blocks of your multi-agent system.

2. **Messages**: Immutable Pydantic-based models for communication between agents.

3. **Promises**: Asynchronous containers for future results, allowing for efficient token streaming and message passing.

4. **Contexts**: `MiniAgents` and `PromisingContext` manage the lifecycle and configuration of agents and promises.

5. **Extensions**: Pre-built agents and utilities for common tasks like dialog management, history tracking, and LLM integration.

## 📄 License

MiniAgents is released under the [MIT License](../../../LICENSE).

## ❓ FAQ

Q: Can I use MiniAgents with other LLM providers besides OpenAI and Anthropic?
A: Yes, you can create custom integrations for other LLM providers by following the patterns in the existing `openai_agent` and `anthropic_agent` implementations.

Q: How does MiniAgents handle error propagation in asynchronous operations?
A: MiniAgents uses a sophisticated error handling mechanism that captures errors in promises and allows them to be propagated or handled gracefully, depending on your configuration.

Q: How does MiniAgents handle concurrency and parallelism?
A: MiniAgents leverages Python's asyncio to handle concurrency. Agents can run concurrently, allowing for efficient parallel processing of tasks.

Q: Can I integrate MiniAgents with existing Python web frameworks?
A: Yes, MiniAgents can be integrated with asynchronous web frameworks like FastAPI or Sanic. You'll need to ensure that the MiniAgents context is properly managed within your web application's lifecycle.

Q: How does the `start_asap` mode differ from regular coroutines?
A: In `start_asap` mode, agents are automatically scheduled to run in the background as soon as they're invoked, without needing explicit awaiting. This allows for more dynamic and responsive agent interactions.

Q: Is it possible to debug MiniAgents applications?
A: Yes, you can use standard Python debugging tools. Additionally, MiniAgents provides logging capabilities that can be enabled for more detailed insights into agent interactions and promise resolutions.

Q: How does MiniAgents ensure message immutability?
A: Messages in MiniAgents are based on Pydantic models with a custom `Frozen` base class, which prevents modifications after creation. This immutability is crucial for maintaining consistency in asynchronous operations.

## 🤝 Contributing

Contributions to MiniAgents are welcome! Here are some ways you can contribute:

1. Report bugs or suggest features by opening issues.
2. Improve documentation.
3. Submit pull requests with bug fixes or new features.

Please read our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## 📚 Documentation

For more detailed documentation, including API references and advanced usage examples, please visit our [Documentation Site](https://miniagents.readthedocs.io).

## 🙏 Acknowledgements

MiniAgents was inspired by various projects in the AI and asynchronous programming communities. We'd like to thank all the open-source contributors whose work has made this project possible.

---

Happy coding with MiniAgents! 🚀 If you have any questions or need assistance, feel free to open an issue on our GitHub repository.
