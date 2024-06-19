"""
This module contains abstractions for chat history management.
"""

from abc import ABC, abstractmethod
from functools import cached_property

from miniagents.messages import Message
from miniagents.miniagent_typing import MessageType
from miniagents.miniagents import InteractionContext, miniagent, MiniAgent, MessageSequence


class ChatHistory(ABC):
    """
    Abstract class for loading chat history from a storage as well as writing new messages to it.
    """

    @cached_property
    def logging_agent(self) -> MiniAgent:
        """
        The agent that logs the chat history to a storage. Replies with the same messages for agent chaining purposes.
        """
        return miniagent(self._logging_agent)

    @abstractmethod
    async def aload_chat_history(self) -> tuple[Message]:
        """
        Load the chat history from the storage.
        """

    @abstractmethod
    async def _logging_agent(self, ctx: InteractionContext) -> None:
        """
        The implementation of the agent that logs the chat history to a storage. Except for logging the messages,
        it also should reply with the same messages for agent chaining purposes.
        """


class InMemoryChatHistory(ChatHistory):
    """
    Class for loading chat history from memory as well as writing new messages to it.
    """

    def __init__(self, default_role: str = "user") -> None:
        super().__init__(default_role=default_role)
        self._chat_history: list[MessageType] = []

    async def _logging_agent(self, ctx: InteractionContext) -> None:
        """
        The implementation of the agent that logs the chat history to memory.
        """
        self._chat_history.extend(ctx.messages)

    async def aload_chat_history(self) -> tuple[Message, ...]:
        """
        Load the chat history from memory.
        """
        return await MessageSequence.aresolve_messages(self._chat_history)
