"""
Test the agents.
"""

import asyncio
from typing import Union

import pytest

from miniagents import InteractionContext, MiniAgents, miniagent
from miniagents.promising.sentinels import Sentinel


@pytest.mark.parametrize("start_soon", [False, True, None])
async def test_agents_run_in_parallel(start_soon: Union[bool, Sentinel]) -> None:
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
        replies1 = agent1.trigger(start_soon=start_soon)
        replies2 = agent2.trigger(start_soon=start_soon)
        if start_soon is False:
            # when agents are not scheduled to start ASAP, their result needs to be awaited for explicitly in order
            # for their respective functions to be called
            await replies1
            await replies2

    if start_soon in [True, None]:
        # `start_soon` is True by default in `MiniAgents()`
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


@pytest.mark.parametrize("start_soon", [False, True, None])
async def test_sub_agents_run_in_parallel(start_soon: Union[bool, Sentinel]) -> None:
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
        ctx.reply([agent.trigger(start_soon=start_soon) for agent in [agent1, agent2]])

    async with MiniAgents():
        replies = aggregation_agent.trigger(start_soon=start_soon)
        if start_soon is False:
            # when agents are not scheduled to start ASAP, their result needs to be awaited for explicitly in order
            # for their respective functions to be called
            await replies

    if start_soon in [True, None]:
        # `start_soon` is True by default in `MiniAgents()`
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


@pytest.mark.parametrize("start_soon", [False, True, None])
async def test_agents_reply_unordered(start_soon: Union[bool, Sentinel]) -> None:
    @miniagent
    async def agent1(ctx: InteractionContext) -> None:
        ctx.reply("agent1 msg1")
        ctx.reply("agent1 msg2")
        ctx.reply(agent2.trigger(start_soon=start_soon))
        ctx.reply("agent1 msg3")
        ctx.reply("agent1 msg4")

    @miniagent
    async def agent2(ctx: InteractionContext) -> None:
        ctx.reply_unordered("agent2 msg1 pre-sleep unordered")
        ctx.reply_unordered("agent2 msg2 pre-sleep unordered")
        await asyncio.sleep(0.1)
        ctx.reply(agent3.trigger(start_soon=start_soon))
        await asyncio.sleep(0.1)
        ctx.reply_unordered("agent2 msg3 post-sleep unordered")
        ctx.reply_unordered("agent2 msg4 post-sleep unordered")

    @miniagent
    async def agent3(ctx: InteractionContext) -> None:
        ctx.reply_unordered("agent3 msg1 pre-sleep unordered")
        ctx.reply_unordered("agent3 msg2 pre-sleep unordered")
        ctx.reply_unordered(agent4.trigger(start_soon=start_soon))
        await asyncio.sleep(0.2)
        ctx.reply_unordered("agent3 msg3 post-sleep unordered")
        ctx.reply_unordered("agent3 msg4 post-sleep unordered")

    @miniagent
    async def agent4(ctx: InteractionContext) -> None:
        await asyncio.sleep(0.3)
        ctx.reply_unordered("agent4 msg1 post-sleep unordered")
        ctx.reply_unordered("agent4 msg2 post-sleep unordered")

    async with MiniAgents():
        replies = await agent1.trigger(start_soon=start_soon)
        replies = [reply.content for reply in replies]

    if start_soon in [True, None]:
        # `start_soon` is True by default in `MiniAgents()`
        assert replies == [
            "agent1 msg1",
            "agent1 msg2",
            "agent2 msg1 pre-sleep unordered",
            "agent2 msg2 pre-sleep unordered",
            "agent3 msg1 pre-sleep unordered",
            "agent3 msg2 pre-sleep unordered",
            "agent2 msg3 post-sleep unordered",
            "agent2 msg4 post-sleep unordered",
            "agent3 msg3 post-sleep unordered",
            "agent3 msg4 post-sleep unordered",
            "agent4 msg1 post-sleep unordered",
            "agent4 msg2 post-sleep unordered",
            "agent1 msg3",
            "agent1 msg4",
        ]
    else:
        assert replies == [
            "agent1 msg1",
            "agent1 msg2",
            "agent2 msg1 pre-sleep unordered",
            "agent2 msg2 pre-sleep unordered",
            "agent2 msg3 post-sleep unordered",
            "agent2 msg4 post-sleep unordered",
            "agent3 msg1 pre-sleep unordered",
            "agent3 msg2 pre-sleep unordered",
            "agent4 msg1 post-sleep unordered",
            "agent4 msg2 post-sleep unordered",
            "agent3 msg3 post-sleep unordered",
            "agent3 msg4 post-sleep unordered",
            "agent1 msg3",
            "agent1 msg4",
        ]


@pytest.mark.parametrize("start_soon", [False, True, None])
async def test_agents_reply_unordered_exception(start_soon: Union[bool, Sentinel]) -> None:
    @miniagent
    async def agent1(ctx: InteractionContext) -> None:
        ctx.reply("agent1 msg1")
        ctx.reply("agent1 msg2")
        ctx.reply(agent2.trigger(start_soon=start_soon))
        ctx.reply("agent1 msg3")
        ctx.reply("agent1 msg4")

    @miniagent
    async def agent2(ctx: InteractionContext) -> None:
        ctx.reply_unordered("agent2 msg1 pre-sleep unordered")
        ctx.reply_unordered("agent2 msg2 pre-sleep unordered")
        await asyncio.sleep(0.1)
        ctx.reply(agent3.trigger(start_soon=start_soon))
        await asyncio.sleep(0.1)
        ctx.reply_unordered("agent2 msg3 post-sleep unordered")
        ctx.reply_unordered("agent2 msg4 post-sleep unordered")

    @miniagent
    async def agent3(ctx: InteractionContext) -> None:
        ctx.reply_unordered("agent3 msg1 pre-sleep unordered")
        ctx.reply_unordered("agent3 msg2 pre-sleep unordered")
        ctx.reply_unordered(agent4.trigger(start_soon=start_soon))
        await asyncio.sleep(0.2)
        ctx.reply_unordered("agent3 msg3 post-sleep unordered")
        ctx.reply_unordered("agent3 msg4 post-sleep unordered")

    @miniagent
    async def agent4(ctx: InteractionContext) -> None:
        await asyncio.sleep(0.3)
        ctx.reply_unordered("agent4 msg1 post-sleep unordered")
        ctx.reply_unordered("agent4 msg2 post-sleep unordered")
        await asyncio.sleep(0.1)  # TODO figure out why the previous two replies are lost if this sleep is removed
        raise ValueError("agent4 exception")

    async with MiniAgents():
        replies = []
        with pytest.raises(ValueError):
            async for reply_promise in agent1.trigger(start_soon=start_soon):
                replies.append((await reply_promise).content)

    if start_soon in [True, None]:
        # `start_soon` is True by default in `MiniAgents()`
        assert replies == [
            "agent1 msg1",
            "agent1 msg2",
            "agent2 msg1 pre-sleep unordered",
            "agent2 msg2 pre-sleep unordered",
            "agent3 msg1 pre-sleep unordered",
            "agent3 msg2 pre-sleep unordered",
            "agent2 msg3 post-sleep unordered",
            "agent2 msg4 post-sleep unordered",
            "agent3 msg3 post-sleep unordered",
            "agent3 msg4 post-sleep unordered",
            "agent4 msg1 post-sleep unordered",
            "agent4 msg2 post-sleep unordered",
            # "agent1 msg3",
            # "agent1 msg4",
        ]
    else:
        assert replies == [
            "agent1 msg1",
            "agent1 msg2",
            "agent2 msg1 pre-sleep unordered",
            "agent2 msg2 pre-sleep unordered",
            "agent2 msg3 post-sleep unordered",
            "agent2 msg4 post-sleep unordered",
            "agent3 msg1 pre-sleep unordered",
            "agent3 msg2 pre-sleep unordered",
            "agent4 msg1 post-sleep unordered",
            "agent4 msg2 post-sleep unordered",
            # "agent3 msg3 post-sleep unordered",
            # "agent3 msg4 post-sleep unordered",
            # "agent1 msg3",
            # "agent1 msg4",
        ]
