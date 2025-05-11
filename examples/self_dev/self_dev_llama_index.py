"""
This module contains the `llama_index_rag_agent` miniagent that uses RAG to answer the user's questions about the
MiniAgents codebase and also the `ingest_repo` function that ingests the MiniAgents repository into the Llama Index
from the local file system using FlatReader.
"""

from functools import cache
from pathlib import Path
from typing import Callable, Union

import nest_asyncio
from dotenv import load_dotenv
from llama_index.core import Settings, StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.agent import ReActAgent
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.indices.base import BaseIndex
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.readers.file import FlatReader

from examples.self_dev.self_dev_common import MINIAGENTS_ROOT, TRANSIENT, FullRepoMessage, RepoFileMessage, mini_agents
from miniagents import InteractionContext, MiniAgent, miniagent
from miniagents.ext.integrations.llama_index import LlamaIndexMiniAgentEmbedding, LlamaIndexMiniAgentLLM
from miniagents.ext.llms import AssistantMessage, OpenAIAgent, openai_embedding_agent

load_dotenv()

LLAMA_INDEX_SOURCE_IDX = TRANSIENT / "llama_index_source_idx"
LLAMA_INDEX_DOCS_IDX = TRANSIENT / "llama_index_docs_idx"

Settings.chunk_size = 512
Settings.chunk_overlap = 64
Settings.llm = LlamaIndexMiniAgentLLM(underlying_miniagent=OpenAIAgent.fork(model="gpt-4o"))
Settings.embed_model = LlamaIndexMiniAgentEmbedding(
    underlying_miniagent=openai_embedding_agent.fork(model="text-embedding-3-large")  # "text-embedding-3-small"
)


@cache
def _load_doc_idx(path: Union[str, Path]) -> BaseIndex:
    storage_context = StorageContext.from_defaults(persist_dir=path)
    return load_index_from_storage(storage_context)


@miniagent
async def llama_index_rag_agent(ctx: InteractionContext, llm_agent: MiniAgent) -> None:
    """
    This agent uses the Llama Index to answer the user's question.
    """
    llm = LlamaIndexMiniAgentLLM(underlying_miniagent=llm_agent)

    individual_query_engine_tools = [
        QueryEngineTool(
            query_engine=_load_doc_idx(LLAMA_INDEX_SOURCE_IDX).as_query_engine(llm=llm),
            metadata=ToolMetadata(
                name="repo_src_vector_index",
                description=(
                    "useful for when you want to answer queries about the MiniAgents repository by looking "
                    "at the source code"
                ),
            ),
        ),
        QueryEngineTool(
            query_engine=_load_doc_idx(LLAMA_INDEX_DOCS_IDX).as_query_engine(llm=llm),
            metadata=ToolMetadata(
                name="repo_doc_vector_index",
                description=(
                    "useful for when you want to answer queries about the MiniAgents repository by looking "
                    "at the documentation"
                ),
            ),
        ),
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

    # TODO is ReActAgent worse that OpenAIAgent from the original example ? What is Chain-of-Abstraction,
    #  btw, and how it works ?
    agent = ReActAgent.from_tools(tools, llm=llm)

    input_messages = [msg for msg in await ctx.message_promises if str(msg) and str(msg).strip()]
    if not input_messages:
        return

    query = str(input_messages[-1])
    chat_history = [
        # TODO the differentiation between user and assistant messages should be standardised somehow
        ChatMessage(content=str(msg), role=getattr(msg, "role", None) or "assistant")
        for msg in input_messages[:-1]
    ]

    response: AgentChatResponse = await agent.achat(message=query, chat_history=chat_history)
    ctx.reply(AssistantMessage(response.response))


async def ingest_repo(
    storage_dir: Union[str, Path] = LLAMA_INDEX_SOURCE_IDX,
    file_filter: Callable[[RepoFileMessage], bool] = lambda _: True,
) -> None:
    """
    Ingest the MiniAgents repository into the Llama Index from the local file system using FlatReader.
    """
    print()
    loader = FlatReader()
    all_docs = []
    for file_msg in FullRepoMessage().repo_files:
        if not file_filter(file_msg):
            continue

        file_docs = loader.load_data(file=MINIAGENTS_ROOT / file_msg.file_posix_path)
        for d in file_docs:
            d.metadata = {"file": file_msg.file_posix_path}
        all_docs.extend(file_docs)
        print(f"{file_msg.file_posix_path} - {len(file_docs)} docs")

    storage_context = StorageContext.from_defaults()
    VectorStoreIndex.from_documents(
        all_docs,
        storage_context=storage_context,
        use_async=True,
    )
    storage_context.persist(persist_dir=storage_dir)


def _is_doc(file_msg: RepoFileMessage) -> bool:
    lower_path = file_msg.file_posix_path.lower()
    return lower_path.endswith(".md") or lower_path.endswith(".rst") or lower_path.endswith("license")


if __name__ == "__main__":
    nest_asyncio.apply()  # VectorStoreIndex.from_documents() starts another event loop internally

    mini_agents.run(ingest_repo(storage_dir=LLAMA_INDEX_SOURCE_IDX, file_filter=lambda f_: not _is_doc(f_)))
    mini_agents.run(ingest_repo(storage_dir=LLAMA_INDEX_DOCS_IDX, file_filter=_is_doc))

    # print the number of newlines in each file in the MiniAgents repository,
    # sort the entries by the number of newlines in descending order
    print()
    for f in sorted(FullRepoMessage().repo_files, reverse=True, key=lambda f_: f_.num_of_newlines):
        print(f.num_of_newlines, "-", f.file_posix_path)
    print()
