"""
Test the agents.
"""

import asyncio
from typing import Union

import pytest

from miniagents.miniagents import MiniAgents, miniagent
from miniagents.promisegraph.sentinels import DEFAULT, Sentinel


@pytest.mark.parametrize("schedule_immediately", [False, True, DEFAULT])
@pytest.mark.asyncio
async def test_agents_run_in_parallel(schedule_immediately: Union[bool, Sentinel]) -> None:
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
        replies1 = agent1.inquire(schedule_immediately=schedule_immediately)
        replies2 = agent2.inquire(schedule_immediately=schedule_immediately)
        if schedule_immediately is False:
            # when agents are not automatically scheduled, their result needs to be awaited for explicitly in order
            # for their respective functions to be called
            await replies1.acollect_messages()
            await replies2.acollect_messages()

    if schedule_immediately is DEFAULT or schedule_immediately is True:
        # for MiniAgents() True is the DEFAULT
        assert event_sequence == [
            "agent1 - start",
            "agent2 - start",
            "agent1 - end",
            "agent2 - end",
        ]
    else:
        # if agents aren't scheduled for execution "immediately" then they are processed sequentially
        assert event_sequence == [
            "agent1 - start",
            "agent1 - end",
            "agent2 - start",
            "agent2 - end",
        ]
