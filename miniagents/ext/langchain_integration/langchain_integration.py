import asyncio

from dotenv import load_dotenv
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

load_dotenv()


async def main() -> None:
    model = ChatOpenAI(model="gpt-4o-2024-05-13")

    messages = [
        HumanMessage(content="Tell me more about the Moon"),
    ]
    async for token in model.astream(messages):
        print(token.content, end="|", flush=True)
    print()

    return
    create_history_aware_retriever()


if __name__ == "__main__":
    asyncio.run(main())
