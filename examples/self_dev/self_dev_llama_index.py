import nest_asyncio
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.readers.file import FlatReader

from examples.self_dev.self_dev_common import FullRepoMessage, MINIAGENTS_ROOT, TRANSIENT, mini_agents


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

    storage_context = StorageContext.from_defaults()
    VectorStoreIndex.from_documents(
        all_docs,
        storage_context=storage_context,
        use_async=True,
    )
    storage_context.persist(persist_dir=TRANSIENT / "llama_index_repo_flat")

    # print the number of newlines in each file in the MiniAgents repository,
    # sort the entries by the number of newlines in descending order
    print()
    for f in sorted(full_repo.repo_files, reverse=True, key=lambda f_: f_.num_of_newlines):
        print(f.num_of_newlines, "-", f.file_posix_path)
    print()


if __name__ == "__main__":
    nest_asyncio.apply()  # VectorStoreIndex.from_documents() starts another event loop internally
    mini_agents.run(ingest_repo())
