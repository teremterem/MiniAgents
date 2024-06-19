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
        The agent that logs the chat history to a storage. Replies with the same messages for agent
        chaining purposes.
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
        The implementation of the agent that logs the chat history to a storage.
        """

    async def _logging_agent_chained(self, ctx: InteractionContext) -> None:
        """
        The implementation of the agent that logs the chat history to a storage.

        ATTENTION! Apart for logging the messages, it also replies with the same messages for agent
        chaining purposes.
        """
        ctx.reply(ctx.messages)  # asynchronously(!) reply with the same messages for agent chaining purposes
        await self._logging_agent(ctx)


class InMemoryChatHistory(ChatHistory):
    """
    Class for loading chat history from memory as well as writing new messages to it.
    """

    def __init__(self) -> None:
        self._chat_history: list[MessageType] = []

    async def _logging_agent(self, ctx: InteractionContext) -> None:
        """
        The implementation of the agent that logs the chat history to memory.
        """
        self._chat_history.append(ctx.messages)

    async def aload_chat_history(self) -> tuple[Message, ...]:
        """
        Load the chat history from memory.
        """
        return await MessageSequence.aresolve_messages(self._chat_history)
