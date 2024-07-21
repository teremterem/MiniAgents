"""
This module contains the `llama_index_rag_agent` miniagent that uses RAG to answer the user's questions about the
MiniAgents codebase and also the `ingest_repo` function that ingests the MiniAgents repository into the Llama Index
from the local file system using FlatReader.
"""

from functools import cache

import nest_asyncio
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex
from llama_index.core import load_index_from_storage, StorageContext
from llama_index.core.agent import ReActAgent
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.indices.base import BaseIndex
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.readers.file import FlatReader

from examples.self_dev.self_dev_common import FullRepoMessage, MINIAGENTS_ROOT, TRANSIENT, mini_agents
from miniagents import InteractionContext, MiniAgent, miniagent
from miniagents.ext.integrations.llama_index import LlamaIndexMiniAgentLLM
from miniagents.ext.llms import AssistantMessage

load_dotenv()

LLAMA_INDEX_STORAGE_DIR = TRANSIENT / "llama_index_repo_flat"

storage_context = StorageContext.from_defaults(persist_dir=LLAMA_INDEX_STORAGE_DIR)


@cache
def _load_doc_index() -> BaseIndex:
    return load_index_from_storage(storage_context)


@miniagent
async def llama_index_rag_agent(ctx: InteractionContext, llm_agent: MiniAgent) -> None:
    """
    This agent uses the Llama Index to answer the user's question.
    """
    llm = LlamaIndexMiniAgentLLM(underlying_miniagent=llm_agent)

    individual_query_engine_tools = [
        QueryEngineTool(
            query_engine=_load_doc_index().as_query_engine(llm=llm),
            metadata=ToolMetadata(
                name="repo_vector_index",
                description="useful for when you want to answer queries about the MiniAgents repository",
            ),
        )
    ]
    query_engine = SubQuestionQueryEngine.from_defaults(
        query_engine_tools=individual_query_engine_tools,
        llm=llm,
    )

    query_engine_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="sub_question_query_engine",
            description=(
                "useful for when you want to answer queries that require analyzing "
                "multiple aspects of the MiniAgents repository"
            ),
        ),
    )

    tools = individual_query_engine_tools + [query_engine_tool]

    # TODO Oleksandr: is ReActAgent worse that OpenAIAgent from the original example ? What is Chain-of-Abstraction,
    #  btw, and how it works ?
    agent = ReActAgent.from_tools(tools, llm=llm)

    input_messages = [msg for msg in await ctx.message_promises if msg.content and msg.content.strip()]
    if not input_messages:
        return

    query = input_messages[-1].content
    chat_history = [
        # TODO Oleksandr: the differentiation between user and assistant messages should be standardised somehow
        ChatMessage(content=msg.content, role=getattr(msg, "role", None) or "assistant")
        for msg in input_messages[:-1]
    ]

    response: AgentChatResponse = await agent.achat(message=query, chat_history=chat_history)
    ctx.reply(AssistantMessage(response.response))


async def ingest_repo() -> None:
    """
    Ingest the MiniAgents repository into the Llama Index from the local file system using FlatReader.
    """
    full_repo = FullRepoMessage()

    loader = FlatReader()
    all_docs = []
    for file_msg in full_repo.repo_files:
        file_docs = loader.load_data(file=MINIAGENTS_ROOT / file_msg.file_posix_path)
        for d in file_docs:
            d.metadata = {"file": file_msg.file_posix_path}
        all_docs.extend(file_docs)
        print(f"{file_msg.file_posix_path} - {len(file_docs)} docs")

    VectorStoreIndex.from_documents(
        all_docs,
        storage_context=storage_context,
        use_async=True,
    )
    storage_context.persist(persist_dir=LLAMA_INDEX_STORAGE_DIR)

    # print the number of newlines in each file in the MiniAgents repository,
    # sort the entries by the number of newlines in descending order
    print()
    for f in sorted(full_repo.repo_files, reverse=True, key=lambda f_: f_.num_of_newlines):
        print(f.num_of_newlines, "-", f.file_posix_path)
    print()


if __name__ == "__main__":
    nest_asyncio.apply()  # VectorStoreIndex.from_documents() starts another event loop internally
    mini_agents.run(ingest_repo())
