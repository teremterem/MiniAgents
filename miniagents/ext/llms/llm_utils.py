"""
Common classes and functions for working with large language models.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union

from pydantic import ConfigDict, Field, BaseModel

from miniagents.ext.agents.history_agents import markdown_llm_logger_agent
from miniagents.messages import Message, MessageTokenAppender, MessagePromise
from miniagents.miniagents import InteractionContext, MiniAgents, MiniAgent
from miniagents.promising.ext.frozen import Frozen


class LLMMessage(Message):
    """
    A message class that is used to interact with large language models (either as input or as output).
    """

    role: str


class UserMessage(LLMMessage):
    """
    A message from a user.
    """

    role: str = "user"


class SystemMessage(LLMMessage):
    """
    A message that is marked as a system message (a concept in large language models).
    """

    role: str = "system"


class AssistantMessage(LLMMessage):
    """
    A message generated by a large language model.
    """

    role: str = "assistant"
    model: Optional[str] = None
    agent_alias: Optional[str] = None


class PromptLogMessage(LLMMessage):
    """
    A message that is a part of a prompt to be logged.
    """


class LLMAgent(ABC, BaseModel):
    """
    A base class for agents that represents various Large Language Models.
    TODO Oleksandr: support OpenAI-style function calls
    TODO Oleksandr: explain parameters
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    ctx: InteractionContext
    model: str
    stream: bool = Field(default_factory=lambda: MiniAgents.get_current().stream_llm_tokens_by_default)
    system: Optional[str] = None
    response_metadata: Optional[Frozen] = None
    response_message_class: type[Message] = AssistantMessage
    llm_logger_agent: Union[MiniAgent, bool] = Field(default_factory=lambda: MiniAgents.get_current().llm_logger_agent)

    async def __call__(self) -> None:
        message_dicts = await self._prepare_message_dicts()

        with MessageTokenAppender(capture_errors=True) as token_appender:
            response_promise = await self._promise_and_close(token_appender)

            if self.llm_logger_agent:
                if self.llm_logger_agent is True:
                    # the default logger agent
                    logger_agent = markdown_llm_logger_agent
                else:
                    logger_agent = self.llm_logger_agent

                logger_agent.kick_off(
                    [
                        self._prompt_messages_to_log(message_dicts),
                        response_promise,
                    ],
                    request_metadata=self._request_metadata_to_log(),
                )

            # here is where the actual request to the LLM is made
            await self._produce_tokens(message_dicts, token_appender)

    @staticmethod
    def _prompt_messages_to_log(message_dicts: list[dict[str, Any]]) -> tuple[PromptLogMessage, ...]:
        """
        TODO Oleksandr: docstring
        """
        return tuple(PromptLogMessage(**message_dict) for message_dict in message_dicts)

    def _request_metadata_to_log(self) -> dict[str, Any]:
        """
        TODO Oleksandr: docstring
        """
        return {
            "agent_alias": self.ctx.this_agent.alias,
            "model": self.model,
            "stream": self.stream,
            # "system": self.system,  # this field usually becomes part of the prompt messages automatically
            **self.__pydantic_extra__,
        }

    @abstractmethod
    async def _prepare_message_dicts(self) -> list[dict[str, Any]]:
        """
        TODO Oleksandr: docstring
        """

    @abstractmethod
    async def _produce_tokens(self, message_dicts: list[dict[str, Any]], token_appender: MessageTokenAppender) -> None:
        """
        TODO Oleksandr: docstring
        """

    async def _promise_and_close(self, token_appender: MessageTokenAppender) -> MessagePromise:
        """
        TODO Oleksandr: docstring
        """
        response_promise = self.response_message_class.promise(
            start_asap=False,  # the agent is already running and will collect tokens anyway (see below)
            message_token_streamer=token_appender,
            # preliminary metadata:
            model=self.model,
            agent_alias=self.ctx.this_agent.alias,
            **dict(self.response_metadata or Frozen()),
        )
        self.ctx.reply(response_promise)
        # we already know that there will be no more response messages, so we close the response sequence
        # (we are closing the sequence of response messages, not the sequence of message tokens)
        await self.ctx.afinish_early()

        return response_promise

    @staticmethod
    def _message_to_llm_dict(message: Message) -> dict[str, Any]:
        """
        Convert a message to a dictionary that can be sent to a large language model.
        """
        try:
            role = message.role
        except AttributeError:
            role = "user"

        return {
            "role": role,
            "content": str(message),
        }
