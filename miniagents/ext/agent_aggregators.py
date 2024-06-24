"""
This module contains agents that are used to aggregate other agents into chains, loops, dialogs and whatnot.
"""

from typing import Union, Iterable

from miniagents.messages import MessageSequencePromise
from miniagents.miniagents import MiniAgent, InteractionContext, miniagent
from miniagents.promising.sentinels import Sentinel, AWAIT, CLEAR


@miniagent
async def dialog_loop_agent(
    ctx: InteractionContext,
    user_agent: Union[MiniAgent, Sentinel],
    assistant_agent: Union[MiniAgent, Sentinel],
) -> None:
    """
    Run a loop that chains the user agent and the assistant agent in a dialog.
    """
    ctx.reply(
        chain_loop_agent.fork(
            agents=[
                user_agent,
                AWAIT,  # TODO Oleksandr: explain this with an inline comment like this one
                assistant_agent,
            ],
        ).inquire(ctx.messages)
    )


@miniagent
async def chain_loop_agent(ctx: InteractionContext, agents: Iterable[Union[MiniAgent, Sentinel]]) -> None:
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
        for agent in agents:
            if agent is None:
                # TODO Oleksandr: explain
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
    # TODO Oleksandr: How should agents end the loop ? What message sequence should this utility return when the
    #  loop is over ?
