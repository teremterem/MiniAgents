from miniagents import InteractionContext, MiniAgents, miniagent


@miniagent
async def some_agent(ctx: InteractionContext) -> None:
    async for msg_promise in ctx.message_promises:
        ctx.reply(f"you said: {await msg_promise}")


async def main() -> None:
    call = some_agent.initiate_call()
    reply_aiter = call.reply_sequence(close_request_sequence=False).__aiter__()

    print("sending hello")
    call.send_message("hello")
    print(await (await reply_aiter.__anext__()))

    print("sending world")
    call.send_message("world")
    print(await (await reply_aiter.__anext__()))


if __name__ == "__main__":
    MiniAgents().run(main())
