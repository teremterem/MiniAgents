from miniagents.miniagents import InteractionContext, miniagent, MiniAgents


@miniagent
async def readme_agent(ctx: InteractionContext) -> None:
    pass


async def amain() -> None:
    reply_sequence = readme_agent.inquire()

    # print()
    # async for msg_promise in reply_sequence:
    #     async for token in msg_promise:
    #         print(f"\033[92;1m{token}\033[0m", end="", flush=True)
    #     print()
    #     print()


if __name__ == "__main__":
    MiniAgents().run(amain())
