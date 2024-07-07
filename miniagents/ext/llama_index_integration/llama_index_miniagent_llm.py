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
    MessageRole,
)
from llama_index.core.llms.callbacks import (
    llm_chat_callback,
    llm_completion_callback,
)
from llama_index.core.llms.llm import LLM

from miniagents import MiniAgent
from miniagents.ext.llm.llm_common import LLMMessage


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
        miniagent_messages = [
            LLMMessage(text=chat_message.content, role=chat_message.role) for chat_message in messages
        ]
        miniagent_response = await self.underlying_miniagent.inquire(miniagent_messages).as_single_promise()

        return ChatResponse(
            message=ChatMessage(
                role=miniagent_response.role,
                content=miniagent_response.text,
                additional_kwargs=miniagent_response.fields_and_values(exclude_text_and_template=True),
            ),
            raw=miniagent_response.model_dump(),
        )

    @llm_chat_callback()
    async def astream_chat(
        self,
        messages: Sequence[ChatMessage],
        **kwargs: Any,
    ) -> ChatResponseAsyncGen:
        miniagent_messages = [
            LLMMessage(text=chat_message.content, role=chat_message.role) for chat_message in messages
        ]
        miniagent_resp_promise = await self.underlying_miniagent.inquire(miniagent_messages).as_single_promise()

        preliminary_metadata = miniagent_resp_promise.preliminary_metadata
        preliminary_metadata_dict = preliminary_metadata.model_dump()
        yield ChatResponse(
            message=ChatMessage(
                role=getattr(preliminary_metadata, "role") or MessageRole.ASSISTANT,
                additional_kwargs=preliminary_metadata.fields_and_values(
                    exclude={"role"}, exclude_text_and_template=True
                ),
            ),
            raw=preliminary_metadata_dict,
        )

        async for token in miniagent_resp_promise:
            yield ChatResponse(
                message=ChatMessage(
                    role=getattr(preliminary_metadata, "role") or MessageRole.ASSISTANT,
                    content=token,
                ),
            )

        miniagent_resp_message = await miniagent_resp_promise
        yield ChatResponse(
            message=ChatMessage(
                role=getattr(miniagent_resp_message, "role") or MessageRole.ASSISTANT,
                additional_kwargs=miniagent_resp_message.fields_and_values(
                    exclude={"role"}, exclude_text_and_template=True
                ),
            ),
            raw=miniagent_resp_message.model_dump(),
        )

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
