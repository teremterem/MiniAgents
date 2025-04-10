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


@pytest.mark.parametrize("start_everything_soon_by_default", [False, True])
async def test_agents_reply_urgently(start_everything_soon_by_default: Union[bool, Sentinel]) -> None:
    @miniagent
    async def agent1(ctx: InteractionContext) -> None:
        ctx.reply("agent 1 msg 1")
        ctx.reply("agent 1 msg 2")
        ctx.reply(agent2.trigger())
        ctx.reply("agent 1 msg 3")
        ctx.reply("agent 1 msg 4")

    @miniagent
    async def agent2(ctx: InteractionContext) -> None:
        ctx.reply_urgently("agent 2 msg 1 PRE-SLEEP high priority")
        ctx.reply_urgently("agent 2 msg 2 PRE-SLEEP high priority")
        await asyncio.sleep(0.1)
        ctx.reply(agent3.trigger())
        await asyncio.sleep(0.1)
        ctx.reply_urgently("agent 2 msg 3 post-sleep high priority")
        ctx.reply_urgently("agent 2 msg 4 post-sleep high priority")

    @miniagent
    async def agent3(ctx: InteractionContext) -> None:
        ctx.reply_urgently("agent 3 msg 1 PRE-SLEEP high priority")
        ctx.reply_urgently("agent 3 msg 2 PRE-SLEEP high priority")
        ctx.reply_urgently(agent4.trigger())
        await asyncio.sleep(0.2)
        ctx.reply_urgently("agent 3 msg 3 post-sleep high priority")
        ctx.reply_urgently("agent 3 msg 4 post-sleep high priority")

    @miniagent
    async def agent4(ctx: InteractionContext) -> None:
        await asyncio.sleep(0.3)
        ctx.reply_urgently("agent 4 msg 1 post-sleep high priority")
        ctx.reply_urgently("agent 4 msg 2 post-sleep high priority")

    async with MiniAgents(start_everything_soon_by_default=start_everything_soon_by_default):
        replies = await agent1.trigger()
        replies = [reply.content for reply in replies]

    if start_everything_soon_by_default in [True, None]:
        # `start_soon` is True by default in `MiniAgents()`
        assert replies == [
            "agent 1 msg 1",
            "agent 1 msg 2",
            "agent 2 msg 1 PRE-SLEEP high priority",
            "agent 2 msg 2 PRE-SLEEP high priority",
            "agent 3 msg 1 PRE-SLEEP high priority",
            "agent 3 msg 2 PRE-SLEEP high priority",
            "agent 2 msg 3 post-sleep high priority",
            "agent 2 msg 4 post-sleep high priority",
            "agent 3 msg 3 post-sleep high priority",
            "agent 3 msg 4 post-sleep high priority",
            "agent 4 msg 1 post-sleep high priority",
            "agent 4 msg 2 post-sleep high priority",
            "agent 1 msg 3",
            "agent 1 msg 4",
        ]
    else:
        assert replies == [
            "agent 1 msg 1",
            "agent 1 msg 2",
            "agent 2 msg 1 PRE-SLEEP high priority",
            "agent 2 msg 2 PRE-SLEEP high priority",
            "agent 2 msg 3 post-sleep high priority",
            "agent 2 msg 4 post-sleep high priority",
            "agent 3 msg 1 PRE-SLEEP high priority",
            "agent 3 msg 2 PRE-SLEEP high priority",
            "agent 4 msg 1 post-sleep high priority",
            "agent 4 msg 2 post-sleep high priority",
            "agent 3 msg 3 post-sleep high priority",
            "agent 3 msg 4 post-sleep high priority",
            "agent 1 msg 3",
            "agent 1 msg 4",
        ]


@pytest.mark.parametrize("start_everything_soon_by_default", [False, True])
@pytest.mark.parametrize("errors_to_messages", [False, True])
async def test_agents_reply_urgently_exception(
    start_everything_soon_by_default: Union[bool, Sentinel], errors_to_messages: bool
) -> None:
    @miniagent
    async def agent1(ctx: InteractionContext) -> None:
        ctx.reply("agent 1 msg 1")
        ctx.reply("agent 1 msg 2")
        ctx.reply(agent2.trigger(errors_to_messages=errors_to_messages))
        ctx.reply("agent 1 msg 3")
        ctx.reply("agent 1 msg 4")

    @miniagent
    async def agent2(ctx: InteractionContext) -> None:
        ctx.reply_urgently("agent 2 msg 1 PRE-SLEEP high priority")
        ctx.reply_urgently("agent 2 msg 2 PRE-SLEEP high priority")
        await asyncio.sleep(0.1)
        ctx.reply(agent3.trigger(errors_to_messages=errors_to_messages))
        await asyncio.sleep(0.1)
        ctx.reply_urgently("agent 2 msg 3 post-sleep high priority")
        ctx.reply_urgently("agent 2 msg 4 post-sleep high priority")

    @miniagent
    async def agent3(ctx: InteractionContext) -> None:
        ctx.reply_urgently("agent 3 msg 1 PRE-SLEEP high priority")
        ctx.reply_urgently("agent 3 msg 2 PRE-SLEEP high priority")
        ctx.reply_urgently(agent4.trigger(errors_to_messages=errors_to_messages))
        await asyncio.sleep(0.2)
        ctx.reply_urgently("agent 3 msg 3 post-sleep high priority")
        ctx.reply_urgently("agent 3 msg 4 post-sleep high priority")

    @miniagent
    async def agent4(ctx: InteractionContext) -> None:
        await asyncio.sleep(0.3)
        ctx.reply_urgently("agent 4 msg 1 post-sleep high priority")
        ctx.reply_urgently("agent 4 msg 2 post-sleep high priority")

        # TODO figure out how to prevent the previous two replies from being lost when the sleep below is removed
        #  (but also make sure that the same problem doesn't happen when the previous two replies are NOT high priority)
        await asyncio.sleep(0.1)
        raise ValueError("agent 4 EXCEPTION")

    async with MiniAgents(start_everything_soon_by_default=start_everything_soon_by_default):
        reply_promises = agent1.trigger(errors_to_messages=errors_to_messages)

        if errors_to_messages:
            actual_replies = await reply_promises
            actual_replies = [reply.content for reply in actual_replies]
        else:
            actual_replies = []
            with pytest.raises(ValueError):
                async for reply_promise in reply_promises:
                    actual_replies.append((await reply_promise).content)

    if start_everything_soon_by_default:
        # `start_soon` is True by default in `MiniAgents()`
        expected_replies = [
            "agent 1 msg 1",
            "agent 1 msg 2",
            "agent 2 msg 1 PRE-SLEEP high priority",
            "agent 2 msg 2 PRE-SLEEP high priority",
            "agent 3 msg 1 PRE-SLEEP high priority",
            "agent 3 msg 2 PRE-SLEEP high priority",
            "agent 2 msg 3 post-sleep high priority",
            "agent 2 msg 4 post-sleep high priority",
            "agent 3 msg 3 post-sleep high priority",
            "agent 3 msg 4 post-sleep high priority",
            "agent 4 msg 1 post-sleep high priority",
            "agent 4 msg 2 post-sleep high priority",
        ]
        if errors_to_messages:
            expected_replies.extend(
                [
                    "ValueError: agent 4 EXCEPTION",
                    "agent 1 msg 3",
                    "agent 1 msg 4",
                ]
            )
    else:
        expected_replies = [
            "agent 1 msg 1",
            "agent 1 msg 2",
            "agent 2 msg 1 PRE-SLEEP high priority",
            "agent 2 msg 2 PRE-SLEEP high priority",
            "agent 2 msg 3 post-sleep high priority",
            "agent 2 msg 4 post-sleep high priority",
            "agent 3 msg 1 PRE-SLEEP high priority",
            "agent 3 msg 2 PRE-SLEEP high priority",
            "agent 4 msg 1 post-sleep high priority",
            "agent 4 msg 2 post-sleep high priority",
        ]
        if errors_to_messages:
            expected_replies.extend(
                [
                    "ValueError: agent 4 EXCEPTION",
                    "agent 3 msg 3 post-sleep high priority",
                    "agent 3 msg 4 post-sleep high priority",
                    "agent 1 msg 3",
                    "agent 1 msg 4",
                ]
            )

    assert actual_replies == expected_replies
