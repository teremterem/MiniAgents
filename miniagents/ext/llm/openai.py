"""
This module integrates OpenAI language models with MiniAgents.
"""

import typing
from functools import cache
from typing import Any

from pydantic import Field, field_validator

from miniagents import Message
from miniagents.ext.llm.llm_common import AssistantMessage, LLMAgent
from miniagents.messages import MessageTokenAppender
from miniagents.miniagents import miniagent

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
    """

    n: int = 1
    async_client: Any = Field(default_factory=_default_openai_client)
    response_message_class: type[Message] = OpenAIMessage

    # noinspection PyNestedDecorators
    @field_validator("n")
    @classmethod
    def _validate_n(cls, n: int) -> int:
        if n != 1:
            raise ValueError("Only n=1 is supported by MiniAgents for AsyncOpenAI().chat.completions.create()")
        return n

    async def _produce_tokens(self, message_dicts: list[dict[str, Any]], token_appender: MessageTokenAppender) -> None:
        """
        TODO Oleksandr: docstring
        """
        openai_response = await self.async_client.chat.completions.create(
            messages=message_dicts, model=self.model, stream=self.stream, n=self.n, **self.__pydantic_extra__
        )
        if self.stream:
            async for chunk in openai_response:
                if len(chunk.choices) != 1:  # TODO Oleksandr: do I really need to check it for every token ?
                    raise RuntimeError(
                        f"exactly one Choice was expected from OpenAI, "
                        f"but {len(openai_response.choices)} were returned instead"
                    )
                token = chunk.choices[0].delta.content
                if token:
                    token_appender.append(token)

                token_appender.metadata_so_far["role"] = (
                    chunk.choices[0].delta.role or token_appender.metadata_so_far["role"]
                )
                self._merge_openai_dicts(
                    token_appender.metadata_so_far,
                    chunk.model_dump(exclude={"choices": {0: {"index": ..., "delta": {"content": ..., "role": ...}}}}),
                )
        else:
            if len(openai_response.choices) != 1:
                raise RuntimeError(
                    f"exactly one Choice was expected from OpenAI, "
                    f"but {len(openai_response.choices)} were returned instead"
                )
            # send the complete message content as a single token
            token_appender.append(openai_response.choices[0].message.content)

            token_appender.metadata_so_far["role"] = openai_response.choices[0].message.role
            token_appender.metadata_so_far.update(
                openai_response.model_dump(
                    exclude={"choices": {0: {"index": ..., "message": {"content": ..., "role": ...}}}}
                )
            )

    async def _prepare_message_dicts(self) -> list[dict[str, Any]]:
        """
        TODO Oleksandr: docstring
        """
        if self.system is None:
            message_dicts = []
        else:
            message_dicts = [
                {
                    "role": "system",
                    "content": self.system,
                },
            ]
        message_dicts.extend(self._message_to_llm_dict(msg) for msg in await self.ctx.message_promises)
        return message_dicts

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
