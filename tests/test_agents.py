"""
Test the agents.
"""

import asyncio
from typing import Union

import pytest

from miniagents import InteractionContext, MiniAgents, miniagent
from miniagents.messages import TextMessage
from miniagents.promising.sentinels import NO_VALUE, Sentinel


@pytest.mark.parametrize("start_soon", [False, True, NO_VALUE])
@pytest.mark.parametrize("reply_out_of_order", [False, True])
@pytest.mark.parametrize("raw_strings", [False, True])
async def test_agent_multiple_replies_without_task_switching(
    start_soon: Union[bool, Sentinel], reply_out_of_order: bool, raw_strings: bool
) -> None:
    """
    Test that an agent can send multiple replies (using both `reply` and `reply_out_of_order` methods) without task
    switching and all of them are delivered.
    """

    @miniagent
    async def agent1(ctx: InteractionContext) -> None:
        if reply_out_of_order:
            reply_method = ctx.reply_out_of_order
        else:
            reply_method = ctx.reply

        def message_factory(content: str) -> TextMessage:
            if raw_strings:
                return content
            return TextMessage(content=content)

        reply_method(message_factory("agent 1 msg 1"))
        reply_method(message_factory("agent 1 msg 2"))
        reply_method(
            [
                message_factory("agent 1 msg 3"),
                message_factory("agent 1 msg 4"),
            ]
        )
        reply_method(message_factory("agent 1 msg 5"))
        reply_method(message_factory("agent 1 msg 6"))

    async with MiniAgents():
        replies = await agent1.trigger(start_soon=start_soon)

    # Even in the case of out-of-order replies, all of them are still delivered in the same order because there is no
    # real agent concurrency and/or nested agents in this test
    assert replies == (
        TextMessage(content="agent 1 msg 1"),
        TextMessage(content="agent 1 msg 2"),
        TextMessage(content="agent 1 msg 3"),
        TextMessage(content="agent 1 msg 4"),
        TextMessage(content="agent 1 msg 5"),
        TextMessage(content="agent 1 msg 6"),
    )


@pytest.mark.parametrize("start_soon", [False, True, NO_VALUE])
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

    if start_soon in [True, NO_VALUE]:
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


async def test_full_duplex_communication():
    @miniagent
    async def some_agent(ctx: InteractionContext) -> None:
        async for msg_promise in ctx.message_promises:
            ctx.reply(f"you said: {await msg_promise}")

    async with MiniAgents():
        call = some_agent.initiate_call()
        reply_aiter = call.reply_sequence(finish_call=False).__aiter__()

        # Test first exchange
        call.send_message("hello")
        response1 = await (await reply_aiter.__anext__())
        assert str(response1) == "you said: hello"

        # Test second exchange
        call.send_message("world")
        response2 = await (await reply_aiter.__anext__())
        assert str(response2) == "you said: world"


@pytest.mark.parametrize("start_soon", [False, True, NO_VALUE])
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

    if start_soon in [True, NO_VALUE]:
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
async def test_agents_reply_out_of_order(start_everything_soon_by_default: bool) -> None:
    @miniagent
    async def agent1(ctx: InteractionContext) -> None:
        ctx.reply("agent 1 msg 1")
        ctx.reply("agent 1 msg 2")
        ctx.reply(agent2.trigger())
        ctx.reply("agent 1 msg 3")
        ctx.reply("agent 1 msg 4")

    @miniagent
    async def agent2(ctx: InteractionContext) -> None:
        ctx.reply_out_of_order("agent 2 msg 1 PRE-SLEEP out-of-order")
        ctx.reply_out_of_order("agent 2 msg 2 PRE-SLEEP out-of-order")
        await asyncio.sleep(0.1)
        ctx.reply(agent3.trigger())
        await asyncio.sleep(0.1)
        ctx.reply_out_of_order("agent 2 msg 3 post-sleep out-of-order")
        ctx.reply_out_of_order("agent 2 msg 4 post-sleep out-of-order")

    @miniagent
    async def agent3(ctx: InteractionContext) -> None:
        ctx.reply_out_of_order("agent 3 msg 1 PRE-SLEEP out-of-order")
        ctx.reply_out_of_order("agent 3 msg 2 PRE-SLEEP out-of-order")
        ctx.reply_out_of_order(agent4.trigger())
        await asyncio.sleep(0.2)
        ctx.reply_out_of_order("agent 3 msg 3 post-sleep out-of-order")
        ctx.reply_out_of_order("agent 3 msg 4 post-sleep out-of-order")

    @miniagent
    async def agent4(ctx: InteractionContext) -> None:
        await asyncio.sleep(0.3)
        ctx.reply_out_of_order("agent 4 msg 1 post-sleep out-of-order")
        ctx.reply_out_of_order("agent 4 msg 2 post-sleep out-of-order")

    async with MiniAgents(start_everything_soon_by_default=start_everything_soon_by_default):
        replies = await agent1.trigger()
        replies = [str(reply) for reply in replies]

    assert replies == [
        "agent 1 msg 1",
        "agent 1 msg 2",
        "agent 2 msg 1 PRE-SLEEP out-of-order",
        "agent 2 msg 2 PRE-SLEEP out-of-order",
        "agent 3 msg 1 PRE-SLEEP out-of-order",
        "agent 3 msg 2 PRE-SLEEP out-of-order",
        "agent 2 msg 3 post-sleep out-of-order",
        "agent 2 msg 4 post-sleep out-of-order",
        "agent 3 msg 3 post-sleep out-of-order",
        "agent 3 msg 4 post-sleep out-of-order",
        "agent 4 msg 1 post-sleep out-of-order",
        "agent 4 msg 2 post-sleep out-of-order",
        "agent 1 msg 3",
        "agent 1 msg 4",
    ]


@pytest.mark.parametrize("start_everything_soon_by_default", [False, True])
@pytest.mark.parametrize("errors_as_messages", [False, True])
@pytest.mark.parametrize("try_out_of_order_in_agent4", [False, True])
async def test_agents_reply_out_of_order_exception(
    start_everything_soon_by_default: bool, errors_as_messages: bool, try_out_of_order_in_agent4: bool
) -> None:
    @miniagent
    async def agent1(ctx: InteractionContext) -> None:
        ctx.reply("agent 1 msg 1")
        ctx.reply("agent 1 msg 2")
        ctx.reply(agent2.trigger())
        ctx.reply("agent 1 msg 3")
        ctx.reply("agent 1 msg 4")

    @miniagent
    async def agent2(ctx: InteractionContext) -> None:
        ctx.reply_out_of_order("agent 2 msg 1 PRE-SLEEP out-of-order")
        ctx.reply_out_of_order("agent 2 msg 2 PRE-SLEEP out-of-order")
        await asyncio.sleep(0.1)
        ctx.reply(agent3.trigger())
        await asyncio.sleep(0.1)
        ctx.reply_out_of_order("agent 2 msg 3 post-sleep out-of-order")
        ctx.reply_out_of_order("agent 2 msg 4 post-sleep out-of-order")

    @miniagent
    async def agent3(ctx: InteractionContext) -> None:
        ctx.reply_out_of_order("agent 3 msg 1 PRE-SLEEP out-of-order")
        ctx.reply_out_of_order("agent 3 msg 2 PRE-SLEEP out-of-order")
        ctx.reply_out_of_order(agent4.trigger())
        await asyncio.sleep(0.2)
        ctx.reply_out_of_order("agent 3 msg 3 post-sleep out-of-order")
        ctx.reply_out_of_order("agent 3 msg 4 post-sleep out-of-order")

    @miniagent
    async def agent4(ctx: InteractionContext) -> None:
        await asyncio.sleep(0.3)
        if try_out_of_order_in_agent4:
            ctx.reply_out_of_order("AGENT 4 MSG 1")
            ctx.reply_out_of_order("AGENT 4 MSG 2")
        else:
            ctx.reply("AGENT 4 MSG 1")
            ctx.reply("AGENT 4 MSG 2")

        # TODO is it ok that without the sleep below, the previous two replies are lost when they are delivered as
        #  out-of-order messages ?
        await asyncio.sleep(0.1)
        raise ValueError("agent 4 EXCEPTION")

    async with MiniAgents(
        start_everything_soon_by_default=start_everything_soon_by_default, errors_as_messages=errors_as_messages
    ):
        reply_promises = agent1.trigger()

        if errors_as_messages:
            actual_replies = await reply_promises
            actual_replies = [str(reply) for reply in actual_replies]
        else:
            actual_replies = []
            with pytest.raises(ValueError):
                async for reply_promise in reply_promises:
                    actual_replies.append(str(await reply_promise))

    expected_replies = [
        "agent 1 msg 1",
        "agent 1 msg 2",
        "agent 2 msg 1 PRE-SLEEP out-of-order",
        "agent 2 msg 2 PRE-SLEEP out-of-order",
        "agent 3 msg 1 PRE-SLEEP out-of-order",
        "agent 3 msg 2 PRE-SLEEP out-of-order",
        "agent 2 msg 3 post-sleep out-of-order",
        "agent 2 msg 4 post-sleep out-of-order",
        "agent 3 msg 3 post-sleep out-of-order",
        "agent 3 msg 4 post-sleep out-of-order",
        "AGENT 4 MSG 1",
        "AGENT 4 MSG 2",
    ]
    if errors_as_messages:
        expected_replies.extend(
            [
                "ValueError: agent 4 EXCEPTION",
                "agent 1 msg 3",
                "agent 1 msg 4",
            ]
        )

    assert actual_replies == expected_replies
