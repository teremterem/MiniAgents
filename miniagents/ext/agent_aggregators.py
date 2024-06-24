# pylint: disable=redefined-outer-name
"""
This module contains agents that are used to aggregate other agents into chains, loops, dialogs and whatnot.
"""

from typing import Union, Iterable, Optional

from miniagents.ext.history_agents import in_memory_history_agent
from miniagents.ext.misc_agents import console_echo_agent, console_prompt_agent
from miniagents.messages import MessageSequencePromise
from miniagents.miniagents import MiniAgent, InteractionContext, miniagent
from miniagents.promising.sentinels import Sentinel, AWAIT, CLEAR


# noinspection PyShadowingNames
@miniagent
async def user_agent(
    ctx: InteractionContext,
    echo_agent: Optional[MiniAgent] = console_echo_agent,
    prompt_agent: Optional[MiniAgent] = console_prompt_agent,
) -> None:
    """
    A user agent that echoes `messages` from the agent that called it, reads the user input and then returns full
    chat history as a reply (so it can be further submitted to an LLM agent, for example).
    TODO Oleksandr: add more details
    """
    ctx.reply(agent_chain.fork(agents=[echo_agent, prompt_agent]).inquire(ctx.messages))


# noinspection PyShadowingNames
@miniagent
async def dialog_loop(
    ctx: InteractionContext,
    assistant_agent: MiniAgent,
    user_agent: MiniAgent = user_agent,
    history_agent: Optional[MiniAgent] = None,
) -> None:
    """
    Run a loop that chains the user agent and the assistant agent in a dialog.
    TODO Oleksandr: add more details
    """
    if not history_agent:
        history_agent = in_memory_history_agent.fork(message_list=[])

    ctx.reply(
        agent_loop.fork(
            agents=[
                user_agent,
                history_agent,
                AWAIT,  # TODO Oleksandr: explain this with an inline comment like this one
                assistant_agent,
            ],
        ).inquire(ctx.messages)
    )


@miniagent
async def agent_loop(ctx: InteractionContext, agents: Iterable[Union[MiniAgent, Sentinel]]) -> None:
    """
    An agent that represents a loop that chains the given agents together in the order they are provided.
    """
    agents = list(agents)
    if not any(agent is AWAIT for agent in agents) or not any(isinstance(agent, MiniAgent) for agent in agents):
        raise ValueError(
            "There should be at least one AWAIT sentinel in the list of agents and at least one real agent "
            "in order for the loop not to schedule the turns infinitely without actually running them."
        )

    messages = ctx.messages
    while True:
        messages = await _achain_agents(agents, messages)
        # TODO Oleksandr: How should the agents end the loop ? What message sequence should be returned
        #  when the loop is over ?


@miniagent
async def agent_chain(ctx: InteractionContext, agents: Iterable[Union[MiniAgent, Sentinel]]) -> None:
    """
    TODO Oleksandr: docstring
    """
    ctx.reply(await _achain_agents(list(agents), ctx.messages))


async def _achain_agents(
    agents: Iterable[Union[MiniAgent, Sentinel]], initial_messages: MessageSequencePromise
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
                messages = await messages.aresolve_messages()
        elif agent is CLEAR:
            messages = None
        elif isinstance(agent, MiniAgent):
            messages = agent.inquire(messages)
        else:
            raise ValueError(f"Invalid agent: {agent}")
    return messages
