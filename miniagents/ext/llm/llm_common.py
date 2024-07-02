"""
Common classes and functions for working with large language models.
"""

from typing import Any, Optional, Type

from miniagents.messages import Message, MessageTokenAppender
from miniagents.miniagents import MiniAgents


class UserMessage(Message):
    """
    A message from a user.
    """

    role: str = "user"


class SystemMessage(Message):
    """
    A message that is marked as a system message (a concept in large language models).
    """

    role: str = "system"


class AssistantMessage(Message):
    """
    A message generated by a large language model.
    """

    role: str = "assistant"
    model: Optional[str] = None
    agent_alias: Optional[str] = None


class LLMAgent:
    """
    A base class for agents that represents various Large Language Models.
    """

    def __init__(
        self, ctx, model: str, stream: Optional[bool] = None, reply_metadata: Optional[dict[str, Any]] = None
    ) -> None:
        self.ctx = ctx
        self.model = model
        self.stream = stream
        self.reply_metadata = reply_metadata

        if self.stream is None:
            self.stream = MiniAgents.get_current().stream_llm_tokens_by_default

    async def _promise_and_close(self, token_appender: MessageTokenAppender, message_class: Type[Message]) -> None:
        """
        TODO Oleksandr
        """
        self.ctx.reply(
            message_class.promise(
                start_asap=False,  # the agent is already running and will collect tokens anyway (see below)
                message_token_streamer=token_appender,
                # preliminary metadata:
                model=self.model,
                agent_alias=self.ctx.this_agent.alias,
                **(self.reply_metadata or {}),
            )
        )
        # we already know that there will be no more response messages, so we close the response sequence
        # (we are closing the sequence of response messages, not the sequence of message tokens)
        self.ctx.finish_early()

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
