"""
Code example for using LLMs.
"""

from pprint import pprint
from typing import Iterable

from dotenv import load_dotenv
from miniagents import Message, MiniAgents
from miniagents.ext import console_output_agent
from miniagents.ext.llms import OpenAIAgent

load_dotenv()

# logging.basicConfig(level=logging.DEBUG)

# llm_agent = AnthropicAgent.fork(model="claude-3-7-sonnet-latest")
llm_agent = OpenAIAgent.fork(model="gpt-4o")

mini_agents = MiniAgents()


@mini_agents.on_persist_messages
async def persist_messages(messages: Iterable[Message]) -> None:
    """
    Print messages to the console.
    """
    for message in messages:
        print("HASH KEY:", message.hash_key)
        print(type(message).__name__)
        pprint(message.serialize(), width=119)
        print()


async def main() -> None:
    """
    Send a message to an LLM agent and print the response.
    """
    console_output_agent.trigger(
        llm_agent.trigger(
            "How are you today?",
            max_tokens=1000,
            temperature=0.0,
            system="Respond only in Yoda-speak.",
        ),
        mention_aliases=False,
    )


if __name__ == "__main__":
    mini_agents.run(main())
