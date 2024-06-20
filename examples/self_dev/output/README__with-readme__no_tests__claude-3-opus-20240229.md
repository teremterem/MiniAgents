# MiniAgents

MiniAgents is an asynchronous Python framework for building multi-agent systems that interact with large language models (LLMs) and other services. It provides a structured way to define, call, and manage agents, making it easier to build complex systems that rely on asynchronous interactions and streaming data.

## Motivation

The motivation behind MiniAgents is to provide a framework that simplifies the process of building agent-based systems that leverage LLMs. It aims to address the following challenges:

- Managing asynchronous interactions between agents and LLMs
- Handling streaming data from LLMs token by token
- Enabling parallel execution of agents
- Providing a structured way to define agents and their interactions
- Ensuring reproducibility through immutable message passing and agent state

MiniAgents provides a high-level abstraction layer that allows developers to focus on defining the behavior of agents and their interactions, while the framework takes care of the low-level details of asynchronous communication, streaming, and message passing.

## Features

- Asynchronous and parallel execution of agents
- Define agents as simple Python functions decorated with `@miniagent`
- Agents can interact with each other by sending and receiving messages
- Agents can send and receive messages asynchronously
- Agents can run in parallel and communicate with each other
- Agents can be composed to create more complex agents
- Agents can be chained together to form complex interaction flows
- Promises and async iterators are used extensively to enable non-blocking communication
- Pass messages between agents using `MessageType` objects
- Integrate with OpenAI and Anthropic LLMs using `create_openai_agent` and `create_anthropic_agent`
- Extensible architecture allows integration with various LLM providers (OpenAI, Anthropic, etc.)
- Supports streaming of messages and tokens for efficient processing
- Utilities for working with message sequences (joining, splitting, etc.)
- Stream tokens from LLMs piece-by-piece using `StreamedPromise`
- Flatten nested message sequences with `MessageSequence`
- Promises and async iterators used extensively to enable non-blocking execution
- Immutable message passing via `Frozen` pydantic models
- Frozen data structures for immutable agent state and message metadata
- Immutable message and agent state for reproducibility
- Built on top of the `Promising` library for managing asynchronous operations
- Asynchronous promise-based programming model with `Promise` and `StreamedPromise`
- Hooks to persist messages as they are sent/received
- Typing with Pydantic for validation and serialization of messages

## Installation

You can install MiniAgents using pip:

```bash
pip install miniagents
```

## Usage

Here's a simple example of defining agents and having them interact:

```python
from miniagents import miniagent, MiniAgents, InteractionContext

@miniagent
async def agent1(ctx: InteractionContext):
    ctx.reply("Hello from Agent 1!")

@miniagent
async def agent2(ctx: InteractionContext):
    message = await ctx.messages.aresolve_messages()
    ctx.reply(f"Agent 2 received: {message[0].text}")

async def main():
    async with MiniAgents():
        agent2_replies = agent2.inquire(agent1.inquire())
        print(await agent2_replies.aresolve_messages())

asyncio.run(main())
```

This will output:
```
(Message(text='Agent 2 received: Hello from Agent 1!'),)
```

For more advanced usage, including integration with LLMs, see the documentation and examples.

### Integrating with OpenAI

You can create an agent that interacts with OpenAI's GPT models:

```python
from dotenv import load_dotenv
from miniagents.ext.llm.openai import create_openai_agent
from miniagents.miniagents import MiniAgents

load_dotenv()

llm_agent = create_openai_agent(model="gpt-4o-2024-05-13")

async def main() -> None:
    async with MiniAgents():
        reply_sequence = llm_agent.inquire("How are you today?", max_tokens=1000, temperature=0.0)
        async for msg_promise in reply_sequence:
            async for token in msg_promise:
                print(token, end="", flush=True)
            print()

if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced Example with Multiple Agents

You can create more complex interactions involving multiple agents:

```python
import asyncio
from miniagents.miniagents import MiniAgents, miniagent, InteractionContext

@miniagent
async def agent1(ctx: InteractionContext) -> None:
    print("Agent 1 is running")
    ctx.reply("Message from Agent 1")

@miniagent
async def agent2(ctx: InteractionContext) -> None:
    print("Agent 2 is running")
    ctx.reply("Message from Agent 2")

@miniagent
async def aggregator_agent(ctx: InteractionContext) -> None:
    ctx.reply([agent1.inquire(), agent2.inquire()])

async def main() -> None:
    async with MiniAgents():
        await aggregator_agent.inquire()

if __name__ == "__main__":
    asyncio.run(main())
```

## Documentation

### Core Concepts

- **MiniAgents**: The main class that manages the lifecycle of agents and their interactions.
- **MiniAgent**: A wrapper for an agent function that allows calling the agent.
- **InteractionContext**: Provides context for the interaction, including the messages and the agent.
- **Message**: Represents a message that can be sent between agents.
- **MessagePromise**: A promise of a message that can be streamed token by token.
- **MessageSequencePromise**: A promise of a sequence of messages that can be streamed message by message.

### Core Classes

- `MiniAgents`: The main context manager for managing agents and their interactions.
- `MiniAgent`: A wrapper for an agent function that allows calling the agent.
- `InteractionContext`: Provides context for an agent's interaction, including the messages and reply streamer.

### Message Handling

- `Message`: Represents a message passed between agents
- `MessagePromise`: A promise that resolves to a message
- `MessageSequencePromise`: A promise of a sequence of messages that can be streamed message by message.

### Promising

- `Promise`: Represents a promise of a value that will be resolved asynchronously.
- `StreamedPromise`: Represents a promise of a whole value that can be streamed piece by piece.
- `StreamAppender`: Allows appending pieces to a stream that is consumed by a `StreamedPromise`.

### Utilities

- `achain_loop`: Runs a loop of agents, chaining their interactions.
- `join_messages`: Joins multiple messages into a single message using a delimiter.
- `split_messages`: Splits messages based on a delimiter.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MiniAgents is released under the [MIT License](LICENSE).

## Things to remember (for the developers of this framework)

- **Different Promise and StreamedPromise resolvers, piece streamers, appenders and what not should always catch
  BaseExceptions and not just Exceptions** when they capture errors to pass those errors as "pieces" in order for
  those errors to be raised at the "consumer side". This is because many of the aforementioned Promising "primitives"
  are often part of mechanisms that involve communications between async tasks via asyncio.Queue objects and just
  interrupting those promises with KeyboardInterrupt which are extended from BaseException instead of letting
  KeyboardInterrupt to go through the queue leads to hanging of those promises (a queue is waiting for END_OF_QUEUE
  sentinel forever but the task that should send it is dead).

---

Happy coding with MiniAgents! 🚀