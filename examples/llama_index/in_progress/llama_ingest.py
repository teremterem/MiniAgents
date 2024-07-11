from pathlib import Path

from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.readers.file import UnstructuredReader

from miniagents.ext.integrations.llama_index import LlamaIndexMiniAgentLLM, LlamaIndexMiniAgentEmbedding
from miniagents.ext.llms import OpenAIAgent, openai_embedding_agent

load_dotenv()

Settings.chunk_size = 512
Settings.chunk_overlap = 64
Settings.llm = LlamaIndexMiniAgentLLM(underlying_miniagent=OpenAIAgent.fork(model="gpt-4o-2024-05-13"))
Settings.embed_model = LlamaIndexMiniAgentEmbedding(
    underlying_embedding=openai_embedding_agent.fork(model="text-embedding-3-small")
)


async def main() -> None:
    years = [2022, 2021, 2020, 2019]

    loader = UnstructuredReader()
    doc_set = {}
    all_docs = []
    for year in years:
        year_docs = loader.load_data(file=Path(f"./data/UBER/UBER_{year}.html"), split_documents=False)
        # insert year metadata into each year
        for d in year_docs:
            d.metadata = {"year": year}
        doc_set[year] = year_docs
        all_docs.extend(year_docs)

    index_set = {}
    for year in years:
        storage_context = StorageContext.from_defaults()
        cur_index = VectorStoreIndex.from_documents(
            doc_set[year],
            storage_context=storage_context,
            use_async=True,
        )
        index_set[year] = cur_index
        storage_context.persist(persist_dir=f"./storage/{year}")
