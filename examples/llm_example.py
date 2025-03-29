"""
Code example for using LLMs.
"""

from pprint import pprint

from dotenv import load_dotenv
from pydantic import BaseModel

from miniagents import Message, MiniAgents
from miniagents.ext import console_output_agent
from miniagents.ext.llms import OpenAIAgent


class Step(BaseModel):
    explanation: str
    output: str


class MathReasoning(BaseModel):
    steps: tuple[Step, ...]
    final_answer: str


load_dotenv()

# logging.basicConfig(level=logging.DEBUG)

# llm_agent = AnthropicAgent.fork(model="claude-3-7-sonnet-latest")
llm_agent = OpenAIAgent.fork(
    model="gpt-4o",
    stream=False,
    mutable_state={
        "response_format": MathReasoning,
        # "response_message_class": MathReasoning,
    },
)

mini_agents = MiniAgents()


# @mini_agents.on_persist_message
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
    resp = llm_agent.trigger(
        "How are you today?",
        max_tokens=1000,
        temperature=0.0,
        system="Respond only in Yoda-speak.",
    )
    console_output_agent.trigger(
        resp,
        mention_aliases=False,
    )
    async for r in resp:
        print(type(r))
        rr = await r
        print(type(rr))


if __name__ == "__main__":
    mini_agents.run(main())
