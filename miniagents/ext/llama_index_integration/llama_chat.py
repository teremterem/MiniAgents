from dotenv import load_dotenv
from llama_index.core import load_index_from_storage, StorageContext, Settings
from llama_index.core.agent import ReActAgent
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata

from miniagents import MiniAgents
from miniagents.ext.llama_index_integration.llama_index_miniagent_llm import LlamaIndexMiniAgentLLM

load_dotenv()

Settings.llm = LlamaIndexMiniAgentLLM()


async def main() -> None:
    years = [2022, 2021, 2020, 2019]

    index_set = {}
    for year in years:
        storage_context = StorageContext.from_defaults(persist_dir=f"./transient/{year}")
        cur_index = load_index_from_storage(
            storage_context,
        )
        index_set[year] = cur_index

    individual_query_engine_tools = [
        QueryEngineTool(
            query_engine=index_set[year].as_query_engine(),
            metadata=ToolMetadata(
                name=f"vector_index_{year}",
                description="useful for when you want to answer queries about the" f" {year} SEC 10-K for Uber",
            ),
        )
        for year in years
    ]

    query_engine = SubQuestionQueryEngine.from_defaults(
        query_engine_tools=individual_query_engine_tools,
    )

    query_engine_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="sub_question_query_engine",
            description=(
                "useful for when you want to answer queries that require analyzing "
                "multiple SEC 10-K documents for Uber"
            ),
        ),
    )

    tools = individual_query_engine_tools + [query_engine_tool]

    # TODO Oleksandr: is ReActAgent worse that OpenAIAgent from the original example ? What is Chain-of-Abstraction,
    #  btw, and how it works ?
    agent = ReActAgent.from_tools(tools, verbose=True)

    # response = agent.chat("hi, i am bob")
    # print(str(response))
    #
    # response = agent.chat("What were some of the biggest risk factors in 2020 for Uber?")
    # print(str(response))

    cross_query_str = (
        "Compare/contrast the risk factors described in the Uber 10-K across" " years. Give answer in bullet points."
    )

    response = await agent.astream_chat(cross_query_str)
    async for token in response.async_response_gen():
        print(token, end="", flush=True)
    print()

    # agent = OpenAIAgent.from_tools(tools)  # verbose=False by default
    #
    # while True:
    #     text_input = input("User: ")
    #     if text_input == "exit":
    #         break
    #     response = agent.chat(text_input)
    #     print(f"Agent: {response}")

    # User: What were some of the legal proceedings against Uber in 2022?


if __name__ == "__main__":
    MiniAgents().run(main())
