"""
Test the agents.
"""

import asyncio

import pytest
from miniagents.miniagents import MiniAgents, miniagent


# TODO Oleksandr: parametrize with different values for `schedule_immediately`
@pytest.mark.asyncio
async def test_agents_run_in_parallel() -> None:
    """
    Test that agents can run in parallel.
    """
    event_sequence = []

    @miniagent
    async def agent1(_) -> None:
        event_sequence.append("agent1 - start")
        asyncio.sleep(1)
        event_sequence.append("agent1 - end")

    @miniagent
    async def agent2(_) -> None:
        event_sequence.append("agent2 - start")
        asyncio.sleep(1)
        event_sequence.append("agent2 - end")

    async with MiniAgents():
        agent1.inquire()
        agent2.inquire()

    assert event_sequence == [
        "agent1 - start",
        "agent2 - start",
        "agent1 - end",
        "agent2 - end",
    ]
