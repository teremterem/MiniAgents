from miniagents import InteractionContext, MiniAgents, miniagent


@miniagent
async def some_agent(ctx: InteractionContext) -> None:
    async for msg_promise in ctx.message_promises:
        ctx.reply(f"you said: {await msg_promise}")


async def main() -> None:
    call = some_agent.initiate_call()
    reply_aiter = aiter(call.reply_sequence(finish_call=False))

    print("sending hello")
    call.send_message("hello")
    print(await (await anext(reply_aiter)))

    print("sending world")
    call.send_message("world")
    print(await (await anext(reply_aiter)))


if __name__ == "__main__":
    MiniAgents().run(main())
