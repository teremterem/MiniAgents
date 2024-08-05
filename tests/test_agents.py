"""
Test the agents.
"""

import asyncio
from typing import Union

import pytest

from miniagents import InteractionContext, MiniAgents, miniagent
from miniagents.promising.sentinels import Sentinel


@pytest.mark.parametrize("start_asap", [False, True, None])
@pytest.mark.asyncio
async def test_agents_run_in_parallel(start_asap: Union[bool, Sentinel]) -> None:
    """
    Test that agents can run in parallel.
    """
    event_sequence = []

    @miniagent
    async def agent1(_) -> None:
        event_sequence.append("agent1 - start")
        await asyncio.sleep(0.1)
        event_sequence.append("agent1 - end")

    @miniagent
    async def agent2(_) -> None:
        event_sequence.append("agent2 - start")
        await asyncio.sleep(0.1)
        event_sequence.append("agent2 - end")

    async with MiniAgents():
        replies1 = agent1.inquire(start_asap=start_asap)
        replies2 = agent2.inquire(start_asap=start_asap)
        if start_asap is False:
            # when agents are not scheduled to start ASAP, their result needs to be awaited for explicitly in order
            # for their respective functions to be called
            await replies1
            await replies2

    if start_asap in [True, None]:
        # `start_asap` is True by default in `MiniAgents()`
        assert event_sequence == [
            "agent1 - start",
            "agent2 - start",
            "agent1 - end",
            "agent2 - end",
        ]
    else:
        # if agents aren't scheduled to start ASAP, then they are processed in this test sequentially
        assert event_sequence == [
            "agent1 - start",
            "agent1 - end",
            "agent2 - start",
            "agent2 - end",
        ]


@pytest.mark.parametrize("start_asap", [False, True, None])
@pytest.mark.asyncio
async def test_sub_agents_run_in_parallel(start_asap: Union[bool, Sentinel]) -> None:
    """
    Test that two agents that were called by the third agent can run in parallel.
    """
    event_sequence = []

    @miniagent
    async def agent1(_) -> None:
        event_sequence.append("agent1 - start")
        await asyncio.sleep(0.1)
        event_sequence.append("agent1 - end")

    @miniagent
    async def agent2(_) -> None:
        event_sequence.append("agent2 - start")
        await asyncio.sleep(0.1)
        event_sequence.append("agent2 - end")

    @miniagent
    async def aggregation_agent(ctx: InteractionContext) -> None:
        # wrapping this generator into a list comprehension is necessary to make sure that the agents are called
        # immediately (and are executed in parallel as a result)
        ctx.reply([agent.inquire(start_asap=start_asap) for agent in [agent1, agent2]])

    async with MiniAgents():
        replies = aggregation_agent.inquire(start_asap=start_asap)
        if start_asap is False:
            # when agents are not scheduled to start ASAP, their result needs to be awaited for explicitly in order
            # for their respective functions to be called
            await replies

    if start_asap in [True, None]:
        # `start_asap` is True by default in `MiniAgents()`
        assert event_sequence == [
            "agent1 - start",
            "agent2 - start",
            "agent1 - end",
            "agent2 - end",
        ]
    else:
        # if agents aren't scheduled to start ASAP, then they are processed in this test sequentially
        assert event_sequence == [
            "agent1 - start",
            "agent1 - end",
            "agent2 - start",
            "agent2 - end",
        ]
