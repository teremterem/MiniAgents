"""
MiniAgent wrapper for llama-index embeddings.
"""

from typing import List

from llama_index.core.base.embeddings.base import BaseEmbedding

from miniagents import MiniAgent


class LlamaIndexMiniAgentEmbedding(BaseEmbedding):  # pylint: disable=too-many-ancestors
    """
    MiniAgent wrapper for llama-index embeddings.
    """

    underlying_miniagent: MiniAgent

    @classmethod
    def class_name(cls) -> str:
        return "llama_index_miniagent_embedding"

    def _get_query_embedding(self, query: str) -> List[float]:
        raise NotImplementedError(
            f"`{self.__class__.__name__}` does not support synchronous operations. "
            f"Use `aget_query_embedding` instead of `get_query_embedding`."
        )

    async def _aget_query_embedding(self, query: str) -> List[float]:
        response_msg = await self.underlying_miniagent.inquire(query).as_single_promise()
        return response_msg.embedding

    def _get_text_embedding(self, text: str) -> List[float]:
        raise NotImplementedError(
            f"`{self.__class__.__name__}` does not support synchronous operations. "
            f"Use `aget_text_embedding` instead of `get_text_embedding`."
        )

    async def _aget_text_embedding(self, text: str) -> List[float]:
        response_msg = await self.underlying_miniagent.inquire(text).as_single_promise()
        return response_msg.embedding

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError(
            f"`{self.__class__.__name__}` does not support synchronous operations. "
            f"Use `aget_text_embeddings` instead of `get_text_embeddings`."
        )

    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        response_messages = await self.underlying_miniagent.inquire(texts, batch_mode=True)
        return [response_msg.embedding for response_msg in response_messages]
