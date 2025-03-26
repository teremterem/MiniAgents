# pylint: disable=too-many-ancestors
"""
Integrations of llama-index with MiniAgents.
"""

from typing import Any, Sequence

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.types import (
    ChatMessage,
    ChatResponse,
    ChatResponseAsyncGen,
    ChatResponseGen,
    CompletionResponse,
    CompletionResponseAsyncGen,
    CompletionResponseGen,
    LLMMetadata,
    MessageRole,
)
from llama_index.core.llms.callbacks import llm_chat_callback, llm_completion_callback
from llama_index.core.llms.llm import LLM

from miniagents.ext.llms.llm_utils import LLMMessage
from miniagents.messages import MESSAGE_CONTENT_FIELD
from miniagents.miniagents import MiniAgent


class LlamaIndexMiniAgentLLM(LLM):
    """
    A proxy from llama-index LLM to a MiniAgent.
    """

    underlying_miniagent: MiniAgent

    @classmethod
    def class_name(cls) -> str:
        return "llama_index_miniagent_llm"

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            is_chat_model=True,
            model_name=self.underlying_miniagent.alias,
        )

    def stream_complete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponseGen:
        raise NotImplementedError(
            f"`{self.__class__.__name__}` does not support synchronous operations. "
            f"Use `astream_complete` instead of `stream_complete`."
        )

    def complete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponse:
        raise NotImplementedError(
            f"`{self.__class__.__name__}` does not support synchronous operations. "
            f"Use `acomplete` instead of `complete`."
        )

    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        raise NotImplementedError(
            f"`{self.__class__.__name__}` does not support synchronous operations. Use `achat` instead of `chat`."
        )

    def stream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponseGen:
        raise NotImplementedError(
            f"`{self.__class__.__name__}` does not support synchronous operations. "
            f"Use `astream_chat` instead of `stream_chat`."
        )

    @llm_chat_callback()
    async def achat(
        self,
        messages: Sequence[ChatMessage],
        **kwargs: Any,
    ) -> ChatResponse:
        miniagent_messages = [LLMMessage(chat_message.content, role=chat_message.role) for chat_message in messages]
        miniagent_response = await self.underlying_miniagent.trigger(miniagent_messages).as_single_promise()

        return ChatResponse(
            message=ChatMessage(
                role=miniagent_response.role,
                content=miniagent_response.content,
                additional_kwargs={
                    key: value for key, value in miniagent_response if key not in ("role", MESSAGE_CONTENT_FIELD)
                },
            ),
            raw=dict(miniagent_response),
        )

    @llm_chat_callback()
    async def astream_chat(
        self,
        messages: Sequence[ChatMessage],
        **kwargs: Any,
    ) -> ChatResponseAsyncGen:
        miniagent_messages = [LLMMessage(chat_message.content, role=chat_message.role) for chat_message in messages]
        miniagent_resp_promise = self.underlying_miniagent.trigger(miniagent_messages).as_single_promise()
        role = getattr(miniagent_resp_promise.preliminary_metadata, "role", None) or MessageRole.ASSISTANT

        async def gen() -> ChatResponseAsyncGen:
            yield ChatResponse(
                message=ChatMessage(
                    role=role,
                    additional_kwargs={
                        key: value for key, value in miniagent_resp_promise.preliminary_metadata if key != "role"
                    },
                ),
                raw=dict(miniagent_resp_promise.preliminary_metadata),
            )

            content = ""
            async for token in miniagent_resp_promise:
                content += token
                yield ChatResponse(
                    message=ChatMessage(
                        role=role,
                        content=content,
                    ),
                    delta=token,
                )

            miniagent_resp_message = await miniagent_resp_promise
            yield ChatResponse(
                message=ChatMessage(
                    role=getattr(miniagent_resp_message, "role", None) or MessageRole.ASSISTANT,
                    content=content,
                    additional_kwargs={
                        key: value
                        for key, value in miniagent_resp_message
                        if key not in ("role", MESSAGE_CONTENT_FIELD)
                    },
                ),
                raw=dict(miniagent_resp_message),
            )

        return gen()

    @llm_completion_callback()
    async def acomplete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponse:
        miniagent_response = await self.underlying_miniagent.trigger(prompt).as_single_promise()

        return CompletionResponse(
            text=miniagent_response.content,
            additional_kwargs={key: value for key, value in miniagent_response if key != MESSAGE_CONTENT_FIELD},
            raw=miniagent_response.model_dump(),
        )

    @llm_completion_callback()
    async def astream_complete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponseAsyncGen:
        miniagent_resp_promise = self.underlying_miniagent.trigger(prompt).as_single_promise()

        async def gen() -> CompletionResponseAsyncGen:
            preliminary_dict = dict(miniagent_resp_promise.preliminary_metadata)
            yield CompletionResponse(additional_kwargs=preliminary_dict, raw=preliminary_dict)

            content = ""
            async for token in miniagent_resp_promise:
                content += token
                yield CompletionResponse(text=content, delta=token)

            miniagent_resp_message = await miniagent_resp_promise
            yield CompletionResponse(
                text=content,
                additional_kwargs={
                    key: value for key, value in miniagent_resp_message if key != MESSAGE_CONTENT_FIELD
                },
                raw=dict(miniagent_resp_message),
            )

        return gen()


class LlamaIndexMiniAgentEmbedding(BaseEmbedding):
    """
    A proxy from llama-index embedding to a MiniAgent.
    """

    underlying_miniagent: MiniAgent

    @classmethod
    def class_name(cls) -> str:
        return "llama_index_miniagent_embedding"

    def _get_query_embedding(self, query: str) -> list[float]:
        raise NotImplementedError(
            f"`{self.__class__.__name__}` does not support synchronous operations. "
            f"Use `aget_query_embedding` instead of `get_query_embedding`."
        )

    async def _aget_query_embedding(self, query: str) -> list[float]:
        response_msg = await self.underlying_miniagent.trigger(query).as_single_promise()
        return response_msg.embedding

    def _get_text_embedding(self, text: str) -> list[float]:
        raise NotImplementedError(
            f"`{self.__class__.__name__}` does not support synchronous operations. "
            f"Use `aget_text_embedding` instead of `get_text_embedding`."
        )

    async def _aget_text_embedding(self, text: str) -> list[float]:
        response_msg = await self.underlying_miniagent.trigger(text).as_single_promise()
        return response_msg.embedding

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError(
            f"`{self.__class__.__name__}` does not support synchronous operations. "
            f"Use `aget_text_embeddings` instead of `get_text_embeddings`."
        )

    async def _aget_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        response_messages = await self.underlying_miniagent.trigger(texts, batch_mode=True)
        return [response_msg.embedding for response_msg in response_messages]
