"""
This module contains agents that are used to aggregate other agents into chains, loops, dialogs and whatnot.
"""

from typing import Union, Iterable, Optional

from miniagents.ext.history_agents import in_memory_history_agent
from miniagents.ext.misc_agents import console_echo_agent, console_prompt_agent
from miniagents.messages import MessageSequencePromise
from miniagents.miniagents import MiniAgent, InteractionContext, miniagent
from miniagents.promising.sentinels import Sentinel, AWAIT, CLEAR

DEFAULT_IN_MEMORY_HISTORY_AGENT = in_memory_history_agent.fork(message_list=[])


@miniagent
async def user_agent(
    ctx: InteractionContext,
    echo_agent: Optional[MiniAgent],
    prompt_agent: Optional[MiniAgent],
    history_agent: Optional[MiniAgent] = DEFAULT_IN_MEMORY_HISTORY_AGENT,
) -> None:
    """
    A user agent that echoes `messages` from the agent that called it, reads the user input and then returns full
    chat history as a reply (so it can be further submitted to an LLM agent, for example).
    TODO Oleksandr: add more details
    """
    ctx.reply(agent_chain.fork(agents=[echo_agent, prompt_agent, history_agent]).inquire(ctx.message_promises))


console_user_agent = user_agent.fork(echo_agent=console_echo_agent, prompt_agent=console_prompt_agent)


# noinspection PyShadowingNames
@miniagent
async def dialog_loop(
    ctx: InteractionContext,
    user_agent: Optional[MiniAgent],  # pylint: disable=redefined-outer-name
    assistant_agent: Optional[MiniAgent],
) -> None:
    """
    Run a loop that chains the user agent and the assistant agent in a dialog.
    TODO Oleksandr: add more details
    """
    ctx.reply(
        agent_loop.fork(
            agents=[
                user_agent,
                AWAIT,  # TODO Oleksandr: explain this with an inline comment
                assistant_agent,
            ],
            raise_keyboard_interrupt=False,
        ).inquire(ctx.message_promises)
    )


@miniagent
async def agent_loop(
    ctx: InteractionContext,
    agents: Iterable[Union[Optional[MiniAgent], Sentinel]],
    raise_keyboard_interrupt: bool = True,
) -> None:
    """
    An agent that represents a loop that chains the given agents together in the order they are provided.
    """
    agents = list(agents)
    if not any(agent is AWAIT for agent in agents) or not any(isinstance(agent, MiniAgent) for agent in agents):
        raise ValueError(
            "There should be at least one AWAIT sentinel in the list of agents and at least one real agent "
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
async def agent_chain(ctx: InteractionContext, agents: Iterable[Union[Optional[MiniAgent], Sentinel]]) -> None:
    """
    TODO Oleksandr: docstring
    """
    ctx.reply(await _achain_agents(list(agents), ctx.message_promises))


async def _achain_agents(
    agents: Iterable[Union[Optional[MiniAgent], Sentinel]], initial_messages: MessageSequencePromise
) -> MessageSequencePromise:
    messages = initial_messages
    for agent in agents:
        if agent is None:
            # it is convenient to accept None as a "no-op" agent - makes it easier to build on top of this
            # function (when some agents are optional in your custom chain or loop function, you can just
            # leave them as None)
            continue

        if agent is AWAIT:
            if isinstance(messages, MessageSequencePromise):
                # all the interactions happen here (here all the scheduled promises are awaited for)
                messages = await messages
        elif agent is CLEAR:
            messages = None
        elif isinstance(agent, MiniAgent):
            messages = agent.inquire(messages)
        else:
            raise ValueError(f"Invalid agent: {agent}")
    return messages
