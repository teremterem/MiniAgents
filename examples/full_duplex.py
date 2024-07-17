"""
TODO Oleksandr: is the name of this script adequate ?
TODO Oleksandr: docstring
"""

from miniagents import MiniAgents, miniagent, InteractionContext


@miniagent
async def some_agent(ctx: InteractionContext) -> None:
    """
    TODO Oleksandr: docstring
    """
    async for msg_promise in ctx.message_promises:
        ctx.reply(f"you said: {await msg_promise}")


async def main() -> None:
    """
    TODO Oleksandr: docstring
    """
    call = some_agent.initiate_inquiry()
    reply_aiter = call.reply_sequence(close_request_sequence=False).__aiter__()

    print("sending hello")
    call.send_message("hello")
    print(await (await reply_aiter.__anext__()))

    print("sending world")
    call.send_message("world")
    print(await (await reply_aiter.__anext__()))


if __name__ == "__main__":
    MiniAgents().run(main())
