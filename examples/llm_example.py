"""
Code example for using LLMs.
"""

from pprint import pprint

from dotenv import load_dotenv

from miniagents import MiniAgents, Message
from miniagents.ext import console_echo_agent
from miniagents.ext.llm import openai_agent

load_dotenv()

# logging.basicConfig(level=logging.DEBUG)

# llm_agent = AnthropicAgent.fork(model="claude-3-haiku-20240307")  # claude-3-opus-20240229
llm_agent = openai_agent.fork(model="gpt-4o-2024-05-13")  # gpt-3.5-turbo-0125

mini_agents = MiniAgents()


@mini_agents.on_persist_message
async def persist_message(_, message: Message) -> None:
    """
    Print the message to the console.
    """
    print("HASH KEY:", message.hash_key)
    print(type(message).__name__)
    pprint(message.serialize(), width=119)
    print()


async def main() -> None:
    """
    Send a message to an LLM agent and print the response.
    """
    console_echo_agent.inquire(
        llm_agent.inquire(
            "How are you today?",
            max_tokens=1000,
            temperature=0.0,
            system="Respond only in Yoda-speak.",
        ),
        mention_aliases=False,
    )


if __name__ == "__main__":
    mini_agents.run(main())
