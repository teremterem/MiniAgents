"""
This module contains agents that are used to aggregate other agents into chains, loops, dialogs and whatnot.
"""

from typing import Iterable, Optional, Union

from miniagents.ext.agents.history_agents import in_memory_history_agent
from miniagents.ext.agents.misc_agents import console_input_agent, console_output_agent
from miniagents.messages import Message, MessageSequencePromise
from miniagents.miniagents import InteractionContext, MiniAgent, miniagent

AWAIT = "AWAIT"
CLEAR = "CLEAR"


@miniagent
async def user_agent(
    ctx: InteractionContext,
    output_agent: Optional[MiniAgent],
    input_agent: Optional[MiniAgent],
    history_agent: Optional[MiniAgent] = in_memory_history_agent,
) -> None:
    """
    A user agent that echoes `messages` from the agent that called it, reads the user input and then returns full
    chat history as a reply (so it can be further submitted to an LLM agent, for example).
    TODO Oleksandr: add more details
    """
    ctx.reply(agent_chain.inquire(ctx.message_promises, agents=[output_agent, input_agent, history_agent]))


console_user_agent = user_agent.fork(output_agent=console_output_agent, input_agent=console_input_agent)


# noinspection PyShadowingNames
@miniagent
async def dialog_loop(
    ctx: InteractionContext,
    user_agent: Optional[MiniAgent],  # pylint: disable=redefined-outer-name
    assistant_agent: Optional[MiniAgent],
) -> None:
    """
    Run a loop that chains the user agent and the assistant agent in a dialog. The `dialog_loop` agent uses
    its own incoming messages as a prompt to the assistant agent and doesn't share his own incoming messages
    the user agent (which also means that they aren't shared with the underlying `history_agent` and don't
    show up in chat history as a result).
    """
    ctx.reply(
        agent_loop.inquire(
            agents=[
                user_agent,
                AWAIT,
                prompt_agent.fork(target_agent=assistant_agent, prompt_prefix=await ctx.message_promises),
            ],
            raise_keyboard_interrupt=False,
        )
    )


@miniagent
async def prompt_agent(
    ctx: InteractionContext,
    target_agent: MiniAgent,
    prompt_prefix: Union[Message, tuple[Message, ...]] = (),
    prompt_suffix: Union[Message, tuple[Message, ...]] = (),
    **target_kwargs,
):
    """
    An agent that prompts the target agent with the given messages and then replies with the target agent's response.
    """
    ctx.reply(
        target_agent.inquire(
            [
                prompt_prefix,
                ctx.message_promises,
                prompt_suffix,
            ],
            **target_kwargs,
        )
    )


@miniagent
async def agent_loop(
    ctx: InteractionContext,
    agents: Iterable[Union[Optional[MiniAgent], str]],
    raise_keyboard_interrupt: bool = True,
) -> None:
    """
    An agent that represents a loop that chains the given agents together in the order they are provided.
    """
    agents = list(agents)
    if not any(agent == AWAIT for agent in agents) or not any(isinstance(agent, MiniAgent) for agent in agents):
        raise ValueError(
            f"There should be at least one {AWAIT!r} sentinel in the list of agents and at least one real agent "
            "in order for the loop not to schedule the turns infinitely without actually running them."
        )

    message_promises = ctx.message_promises
    try:
        while True:
            message_promises = await _achain_agents(agents, message_promises)
    except KeyboardInterrupt:
        if raise_keyboard_interrupt:
            raise


@miniagent
async def agent_chain(ctx: InteractionContext, agents: Iterable[Union[Optional[MiniAgent], str]]) -> None:
    """
    TODO Oleksandr: docstring
    """
    ctx.reply(await _achain_agents(list(agents), ctx.message_promises))


async def _achain_agents(
    agents: Iterable[Union[Optional[MiniAgent], str]], initial_messages: MessageSequencePromise
) -> MessageSequencePromise:
    messages = initial_messages
    for agent in agents:
        if agent is None:
            # it is convenient to accept None as a "no-op" agent - makes it easier to build on top of this
            # function (when some agents are optional in your custom chain or loop function, you can just
            # leave them as None)
            continue

        if agent == AWAIT:
            if isinstance(messages, MessageSequencePromise):
                # all the interactions happen here (here all the scheduled promises are awaited for)
                messages = await messages
        elif agent == CLEAR:
            messages = None
        elif isinstance(agent, MiniAgent):
            messages = agent.inquire(messages)
        else:
            raise ValueError(f"Invalid agent: {agent}")
    return messages
