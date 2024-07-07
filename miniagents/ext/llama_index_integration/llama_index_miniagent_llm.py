from typing import Any, Sequence

from llama_index.core.base.llms.types import (
    ChatMessage,
    ChatResponse,
    ChatResponseAsyncGen,
    ChatResponseGen,
    CompletionResponse,
    CompletionResponseAsyncGen,
    LLMMetadata,
    CompletionResponseGen,
)
from llama_index.core.llms.callbacks import (
    llm_chat_callback,
    llm_completion_callback,
)
from llama_index.core.llms.llm import LLM

from miniagents import MiniAgent


class LlamaIndexMiniAgentLLM(LLM):
    underlying_miniagent: MiniAgent

    @classmethod
    def class_name(cls) -> str:
        return "llama_index_miniagent_llm"

    @property
    def metadata(self) -> LLMMetadata:
        # TODO Oleksandr: fill this in
        return LLMMetadata()

    def stream_complete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponseGen:
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support synchronous model completion. "
            f"Use `astream_complete` instead of `stream_complete`."
        )

    def complete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponse:
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support synchronous model completion. "
            f"Use `acomplete` instead of `complete`."
        )

    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support synchronous model completion. "
            f"Use `achat` instead of `chat`."
        )

    def stream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponseGen:
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support synchronous model completion. "
            f"Use `astream_chat` instead of `stream_chat`."
        )

    @llm_chat_callback()
    async def achat(
        self,
        messages: Sequence[ChatMessage],
        **kwargs: Any,
    ) -> ChatResponse:
        return self.chat(messages, **kwargs)

    @llm_chat_callback()
    async def astream_chat(
        self,
        messages: Sequence[ChatMessage],
        **kwargs: Any,
    ) -> ChatResponseAsyncGen:
        async def gen() -> ChatResponseAsyncGen:
            for message in self.stream_chat(messages, **kwargs):
                yield message

        # NOTE: convert generator to async generator
        return gen()

    @llm_completion_callback()
    async def acomplete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponse:
        return self.complete(prompt, formatted=formatted, **kwargs)

    @llm_completion_callback()
    async def astream_complete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponseAsyncGen:
        async def gen() -> CompletionResponseAsyncGen:
            for message in self.stream_complete(prompt, formatted=formatted, **kwargs):
                yield message

        # NOTE: convert generator to async generator
        return gen()
