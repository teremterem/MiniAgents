"""
This module integrates OpenAI language models with MiniAgents.
"""

import typing
from functools import cache
from typing import Any, Optional, Union

from pydantic import Field, field_validator

from miniagents.ext.agents.history_agents import markdown_llm_logger_agent
from miniagents.ext.llms.llm_utils import (
    AssistantMessage,
    EmbeddingMessage,
    LLMAgent,
    PromptLogMessage,
    message_to_llm_dict,
)
from miniagents.messages import Message, MessageSequence, MessageTokenAppender
from miniagents.miniagent_typing import MessageType
from miniagents.miniagents import InteractionContext, MiniAgent, MiniAgents, miniagent
from miniagents.promising.ext.frozen import Frozen

if typing.TYPE_CHECKING:
    import openai as openai_original


class OpenAIMessage(AssistantMessage):
    """
    A message generated by an OpenAI model.
    """


@cache
def _default_openai_client() -> "openai_original.AsyncOpenAI":
    try:
        # pylint: disable=import-outside-toplevel
        # noinspection PyShadowingNames
        import openai as openai_original
    except ModuleNotFoundError as exc:
        raise ImportError(
            "The 'openai' package is required for the 'openai' extension of MiniAgents. "
            "Please install it via 'pip install -U openai'."
        ) from exc

    return openai_original.AsyncOpenAI()


@miniagent
class OpenAIAgent(LLMAgent):
    """
    An agent that represents Large Language Models by OpenAI. Check out the implementation of the async `__call__`
    method in the base class `LLMAgent` to understand how agents like this one work (the two most important methods
    of all class-based miniagents are `__init__` and `__call__`).
    TODO explain parameters
    """

    n: int = 1
    async_client: Any = Field(default_factory=_default_openai_client)
    response_message_class: type[Message] = OpenAIMessage

    # noinspection PyNestedDecorators
    @field_validator("n")
    @classmethod
    def _validate_n(cls, n: int) -> int:
        # TODO stop complaining about n, support batch mode instead
        if n != 1:
            raise ValueError("Only n=1 is supported by MiniAgents for AsyncOpenAI().chat.completions.create()")
        return n

    async def _aprepare_message_dicts(self) -> list[dict[str, Any]]:
        return await aprepare_dicts_for_openai(self.ctx.message_promises, system=self.system)

    async def _aproduce_tokens(
        self, message_dicts: list[dict[str, Any]], token_appender: MessageTokenAppender
    ) -> None:
        openai_response = await self.async_client.chat.completions.create(
            messages=message_dicts, model=self.model, stream=self.stream, n=self.n, **self.__pydantic_extra__
        )
        if self.stream:
            async for chunk in openai_response:
                if len(chunk.choices) != 1:  # TODO do I really need to check it for every token ?
                    raise RuntimeError(
                        f"exactly one Choice was expected from OpenAI, "
                        f"but {len(openai_response.choices)} were returned instead"
                    )
                # TODO put all the token metadata into the token
                token_appender.append(self.response_message_class.token_class()(chunk.choices[0].delta.content))

                token_appender.auxiliary_field_collector["role"] = (
                    chunk.choices[0].delta.role or token_appender.auxiliary_field_collector["role"]
                )
                self._merge_openai_dicts(
                    token_appender.auxiliary_field_collector,
                    chunk.model_dump(exclude={"choices": {0: {"index": ..., "delta": {"content": ..., "role": ...}}}}),
                )
        else:
            if len(openai_response.choices) != 1:
                raise RuntimeError(
                    f"exactly one Choice was expected from OpenAI, "
                    f"but {len(openai_response.choices)} were returned instead"
                )
            # send the complete message content as a single token
            # TODO put all the token metadata into the token too (in this case metadata of complete message)
            token_appender.append(
                self.response_message_class.token_class()(openai_response.choices[0].message.content)
            )

            token_appender.auxiliary_field_collector["role"] = openai_response.choices[0].message.role
            token_appender.auxiliary_field_collector.update(
                openai_response.model_dump(
                    exclude={"choices": {0: {"index": ..., "message": {"content": ..., "role": ...}}}}
                )
            )

    @classmethod
    def _merge_openai_dicts(cls, destination_dict: dict[str, Any], dict_to_merge: dict[str, Any]) -> None:
        """
        Merge the dict_to_merge into the destination_dict.
        """
        for key, value in dict_to_merge.items():
            if value is not None:
                existing_value = destination_dict.get(key)
                if isinstance(existing_value, dict):
                    cls._merge_openai_dicts(existing_value, value)
                elif isinstance(existing_value, list):
                    if key == "choices":
                        if not existing_value:
                            destination_dict[key] = [{}]  # we only expect a single choice in our implementation
                        cls._merge_openai_dicts(destination_dict[key][0], value[0])
                    else:
                        destination_dict[key].extend(value)
                else:
                    destination_dict[key] = value


async def aprepare_dicts_for_openai(messages: MessageType, *, system: Optional[str] = None) -> list[dict[str, Any]]:
    message_dicts = [message_to_llm_dict(msg) for msg in await MessageSequence.turn_into_sequence_promise(messages)]
    if system:
        message_dicts.append(
            {
                "role": "system",
                "content": system,
            },
        )
    return message_dicts


@miniagent
async def openai_embedding_agent(
    ctx: InteractionContext,
    model: str,
    *,
    async_client: Any = None,
    batch_mode: bool = False,
    response_metadata: Optional[Frozen] = None,
    llm_logger_agent: Optional[Union[MiniAgent, bool]] = None,
    **kwargs,
) -> None:
    """
    An agent that produces embedding(s) for text(s) of the provided message(s) using OpenAI embedding models.

    Args:
        ctx: The interaction context provided by the MiniAgents framework.
        model: The OpenAI embedding model to use.
        async_client: An optional AsyncOpenAI client to use. If None, a default client will be created.
        batch_mode: When True, produces separate embeddings for each input message.
                    When False (default), concatenates all input messages into a single text before embedding.
        response_metadata: Optional metadata to include in the embedding response messages.
        llm_logger_agent: An agent for logging LLM interactions,
                          True to use `markdown_llm_logger_agent`,
                          None (default) to inherit this setting from the global MiniAgents context.
        **kwargs: Additional keyword arguments to pass to the OpenAI embeddings API.
    """
    if not async_client:
        async_client = _default_openai_client()

    if llm_logger_agent is None:
        llm_logger_agent = MiniAgents.get_current().llm_logger_agent
    if llm_logger_agent is True:
        llm_logger_agent = markdown_llm_logger_agent

    if batch_mode:
        # we are in batch mode - let's collect all the messages and produce embeddings for each of them
        texts = [str(await msg_promise) async for msg_promise in ctx.message_promises]
    else:
        # if we are not in batch mode, and we still receive multiple messages, we will concatenate them all into
        # a single piece of text with parts (messages) separated by double newlines
        texts = [str(await ctx.message_promises.as_single_text_promise())]

    data = (await async_client.embeddings.create(input=texts, model=model, **kwargs)).data

    response_metadata_dict = dict(response_metadata or {})

    embedding_messages = [EmbeddingMessage(embedding=entry.embedding, **response_metadata_dict) for entry in data]
    ctx.reply(embedding_messages)

    if llm_logger_agent:
        llm_logger_agent.trigger(
            list(zip([PromptLogMessage(content=text, role="user") for text in texts], embedding_messages)),
            request_metadata={
                "agent_alias": ctx.this_agent.alias,
                "model": model,
                "batch_mode": batch_mode,
                **kwargs,
            },
            show_response_metadata=False,
        )
