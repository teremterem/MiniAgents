"""
This module integrates OpenAI language models with MiniAgents.
"""

import logging
import typing
from functools import cache
from pprint import pformat
from typing import Any, Optional

from miniagents.ext.llm.llm_common import AssistantMessage, LLMAgent
from miniagents.messages import MessageTokenAppender
from miniagents.miniagents import MiniAgent, miniagent, InteractionContext

if typing.TYPE_CHECKING:
    import openai as openai_original

logger = logging.getLogger(__name__)


class OpenAIMessage(AssistantMessage):
    """
    A message generated by an OpenAI model.
    """


# this is for pylint to understand that `OpenAIAgent` becomes an instance of `MiniAgent` after decoration
OpenAIAgent: MiniAgent


@miniagent
class OpenAIAgent(LLMAgent):
    """
    An agent that represents Large Language Models by OpenAI.
    """

    def __init__(
        self,
        ctx: InteractionContext,
        model: str,
        stream: Optional[bool] = None,
        system: Optional[str] = None,
        n: int = 1,
        async_client: Optional["openai_original.AsyncOpenAI"] = None,
        reply_metadata: Optional[dict[str, Any]] = None,
        **other_kwargs,
    ) -> None:
        if n != 1:
            raise ValueError("Only n=1 is supported by MiniAgents for AsyncOpenAI().chat.completions.create()")

        super().__init__(ctx=ctx, model=model, stream=stream, reply_metadata=reply_metadata)
        self.system = system
        self.async_client = async_client or _default_openai_client()
        self.other_kwargs = other_kwargs

        self._message_class = OpenAIMessage

    async def __call__(self) -> None:
        message_dicts = await self._prepare_message_dicts()

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("SENDING TO LLM:\n\n%s\n", pformat(message_dicts))

        with MessageTokenAppender(capture_errors=True) as token_appender:
            await self._promise_and_close(token_appender, self._message_class)
            await self._produce_tokens(message_dicts, token_appender)

    async def _produce_tokens(self, message_dicts: list[dict[str, Any]], token_appender: MessageTokenAppender) -> None:
        """
        TODO Oleksandr: docstring
        """
        openai_response = await self.async_client.chat.completions.create(
            messages=message_dicts, model=self.model, stream=self.stream, **self.other_kwargs
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
            # send the complete message text as a single token
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
