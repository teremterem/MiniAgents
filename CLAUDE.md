# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## MiniAgents: Multi-Agent AI Framework With Procedural Simplicity

An open-source, async-first Python framework for building multi-agent AI systems with an innovative approach to parallelism, so you can focus on creating intelligent agents, not on managing the concurrency of your flows.

## Development Commands

### Setup and Installation
```bash
# Install with dev dependencies using uv (the project's package manager)
uv sync --all-extras

# Or install specific extras
uv sync --extra dev
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov

# Run a single test file
pytest tests/test_specific.py

# Run a specific test
pytest tests/test_specific.py::test_name
```

### Code Quality
```bash
# Format code with black (line-length=119)
black .

# Lint code with pylint
pylint miniagents

# Run all pre-commit hooks
pre-commit run --all-files

# Format and lint Python files after editing
black <file.py> && pylint <file.py>
```

### Building and Publishing
```bash
# Build the package
uv build

# Lock dependencies
uv lock

# View dependency tree
uv tree
```

## High-Level Architecture

### Core Design Principles

1. **Promise-Based Architecture**: The framework uses a sophisticated promise/streaming system enabling:
   - Lazy evaluation and streaming of data
   - Replayable message sequences (unlike standard async generators)
   - Automatic parallelism without explicit concurrency management
   - Non-blocking agent communication

2. **Immutable Message Philosophy**: Messages are Pydantic-based immutable objects, eliminating race conditions and enabling safe parallel execution.

3. **Sequence Flattening**: The framework automatically flattens nested message structures from multiple agents into linear sequences, enabling seamless parallel execution while maintaining procedural code style.

### Key Architecture Components

```
miniagents/
├── promising/                    # Core promise/streaming infrastructure
│   ├── promising.py             # Base Promise, StreamedPromise, PromisingContext
│   ├── sequence.py              # FlatSequence for automatic sequence flattening
│   └── ext/frozen.py            # Immutable data structures
├── miniagents.py                # Core framework classes (MiniAgent, InteractionContext)
├── messages.py                  # Message system (Message, MessagePromise, MessageSequence)
└── ext/                         # Extensions
    ├── llms/                    # LLM integrations (OpenAI, Anthropic)
    └── agents/                  # Pre-built utility agents
```

### Agent Definition and Execution

Agents are defined using the `@miniagent` decorator:
```python
@miniagent
async def my_agent(ctx: InteractionContext, **kwargs) -> None:
    # Access input via ctx.message_promises
    # Send output via ctx.reply() or ctx.reply_out_of_order()
```

Key execution patterns:
- `agent.trigger()` returns immediately with a `MessageSequencePromise`
- No `await` on trigger = parallel execution
- `agent.fork()` creates isolated instances with specific configurations
- `agent.initiate_call()` allows incremental message feeding

### Promise System Architecture

Three-layer promise architecture:
1. **Base Promise Layer**: Basic promise with lazy resolution
2. **Streamed Promise Layer**: Replayable streaming with piece-by-piece delivery
3. **Message Promise Layer**: Specialized for agent communication with token streaming

### Error Handling

- `errors_as_messages=True`: Converts exceptions to ErrorMessage objects
- `error_tracebacks_in_messages=True`: Include full traceback in error messages
- Local overrides possible via `errors_as_messages=False` in trigger calls

## Code Style Requirements

1. **Python Version**: 3.10+ required
2. **Formatting**: Use black with line-length=119
3. **Linting**: All pylint errors must be fixed
4. **Exceptions**: Always use `raise X from Y` to preserve exception chains
5. **Pre-commit**: Run hooks before committing

## Testing Guidelines

- Framework uses pytest with asyncio support
- Coverage tracking is enabled
- Test individual agents in isolation before integration

## Key Patterns for Development

### Basic Agent Pattern
```python
@miniagent
async def processor_agent(ctx: InteractionContext, config_param: str) -> None:
    # Process input
    input_text = await ctx.message_promises.as_single_text_promise()

    # Trigger sub-agents in parallel
    ctx.reply_out_of_order([
        sub_agent1.trigger(ctx.message_promises),
        sub_agent2.trigger(ctx.message_promises),
    ])

    # Stream results
    ctx.reply(final_agent.trigger(ctx.message_promises))
```

### Agent Forking for State
```python
# Create agent with mutable state
stateful_agent = base_agent.fork(
    non_freezable_kwargs={"some_cache": {}, "some_mutable_list": []}
)
```

### Incremental Message Feeding
```python
# Start a call
call = target_agent.initiate_call(initial_data=data)

# Send messages incrementally
for result in results:
    call.send_message(result)

# Get final response
ctx.reply(call.reply_sequence())
```

## Running Examples

```bash
# Basic conversation example
python examples/conversation.py

# LLM integration example
python examples/llm_example.py

# Complex web research system
python examples/web_research_tutorial/web_research.py
```

## Important Notes

- LLM integrations require API keys (OpenAI, Anthropic)
- Use `llm_logger_agent=True` for debugging LLM interactions
- Framework handles concurrency automatically - avoid manual asyncio task management
- Messages are immutable - create new messages rather than modifying existing ones
