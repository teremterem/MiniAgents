"""
WebResearch is a multi-agent system that:

1. Breaks down a user's question into search queries
2. Executes searches in parallel
3. Analyzes search results to identify relevant web pages
4. Scrapes and extracts information from those pages
5. Synthesizes a comprehensive answer

All the agents are built using the MiniAgents framework.
Please refer to the README.md of this repository to learn how to run the application.
"""

import asyncio
from datetime import datetime
from typing import Union

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel

from utils import check_miniagents_version, fetch_google_search, scrape_web_page

check_miniagents_version()

# pylint: disable=wrong-import-position
from miniagents import AgentCall, InteractionContext, Message, MessageSequencePromise, MiniAgents, miniagent
from miniagents.ext.llms import OpenAIAgent, aprepare_dicts_for_openai

load_dotenv()

MODEL = "gpt-4o-mini"  # "gpt-4o"
SMARTER_MODEL = "o4-mini"  # "o3"
MAX_WEB_PAGES_PER_SEARCH = 2
SLEEP_BEFORE_RETRY_SEC = 5

openai_client = AsyncOpenAI()


async def main():
    question = input("\nEnter your question: ")

    # Invoke the main agent (no `await` is placed in front of the call, hence this is a non-blocking operation, no
    # processing starts just yet)
    response_promises: MessageSequencePromise = research_agent.trigger(question)

    print()
    # Iterate over the individual message promises in the response sequence promise. The async loops below lead to task
    # switching, so the agent above as well as its "sub-agents" will now start their work in the background to serve
    # all the promises.
    async for message_promise in response_promises:
        # Skip messages that are not intended for the user. The `known_beforehand` attribute of a `MessagePromise`
        # allows access to metadata that is available before the message content itself is resolved. This can be useful
        # for early filtering or routing of messages. Here, we use it to check the "not_for_user" flag, which is set in
        # `page_scraper_agent` to prevent internal page summaries from being directly displayed to the user.
        if message_promise.known_beforehand.get("not_for_user"):
            continue
        # Iterate over the individual tokens in the message promise (messages that aren't broken down into tokens will
        # be delivered in a single token)
        async for token in message_promise:
            print(token, end="", flush=True)
        print("\n")

    # NOTE #1: The `print` statements above are the only `print` statements in the whole application (except for just
    # one other `print` statement in `utils.py` which reports if the installed version of MiniAgents is too old and
    # needs to be updated).
    #
    # This is because all the agents communicate everything back here, including their progress and their failures.
    # None of the agents declared in this file print anything to the console on their own! In future examples I will
    # demonstrate how easy it is to swap the UI as a consequence of this design (or even connect this whole agentic
    # system to another, bigger AI system instead of exposing it to the user directly).
    #
    # NOTE #2: Even though we are consuming the promises in the loops above explicitly, this is not strictly required
    # for the agents to start their work in the background. By default, they will start in the background regardless of
    # the reason for switching tasks (even if, instead of the agent response promises, we awaited for something
    # completely different).
    #
    # Such behaviour could be prevented by setting `start_soon` to False. However, we do not recommend doing so for the
    # whole system globally. You could pass `start_soon=False` into `trigger` here and there if you absolutely needed
    # to prevent some agent or agents from processing in the background until you explicitly `await` for their
    # responses, but setting it to False at the level of the global `MiniAgents` instance
    # (`MiniAgents(start_everything_soon_by_default=False).run(<app_entrypoint>)` or similar) often leads to deadlocks
    # when the agent interdependencies are more complex.
    #
    # In the majority of scenarios there is hardly any benefit in setting `start_soon` to False for anything.


@miniagent
async def research_agent(ctx: InteractionContext) -> None:
    ctx.reply("RESEARCHING...")

    # First, analyze the user's question and break it down into search queries
    message_dicts = await aprepare_dicts_for_openai(
        ctx.message_promises,
        system=(
            "Your job is to breakdown the user's question into a list of web searches that need to be done to answer "
            "the question. Please try to optimize your search queries so there aren't too many of them. Current date "
            "is " + datetime.now().strftime("%Y-%m-%d")
        ),
    )
    # There is no built-in miniagent for OpenAI's Structured Output feature (yet), so we will use OpenAI's client
    # library directly
    response = await openai_client.beta.chat.completions.parse(
        model=SMARTER_MODEL,
        messages=message_dicts,
        response_format=WebSearchesToBeDone,  # See the definition of this class at the bottom of this file
    )
    parsed: WebSearchesToBeDone = response.choices[0].message.parsed

    ctx.reply(f"RUNNING {len(parsed.web_searches)} WEB SEARCHES")

    already_picked_urls = set[str]()
    # Let's fork the `web_search_agent` to introduce mutable state - we want it to remember across multiple calls
    # which urls were already picked for scraping, so it doesn't scrape them again (same pages may be present in
    # multiple search results)
    _web_search_agent = web_search_agent.fork(
        non_freezable_kwargs={
            "already_picked_urls": already_picked_urls,
        },
    )

    # We will initiate a call to the final answer agent because we will be collecting input for it as we go along
    # (unlike `trigger`, `initiate_call` does not require all the input messages and/or promises upfront)
    final_answer_call: AgentCall = final_answer_agent.initiate_call(
        # We will deliver the dialog with the user (which in this version of the app consists of only the user
        # question) to the `final_answer_agent` as a keyword argument, because the input sequence will be used to pass
        # the information found on the internet to answer the question. (Every miniagent receives a promise of the
        # input sequence of message promises, keyword arguments, and spews out a promise of the reply sequence of
        # message promises.)
        user_question=await ctx.message_promises,
    )

    # For each identified search query, trigger a web search
    for web_search in parsed.web_searches:
        # No `await` in front of `trigger` means no blocking. A promise of a message sequence is placed into
        # `search_and_scraping_results` instead.
        search_and_scraping_results = _web_search_agent.trigger(
            ctx.message_promises,
            search_query=web_search.web_search_query,
            rationale=web_search.rationale,
        )
        # Unlike regular `reply`, `reply_out_of_order` doesn't enforce the order of the messages, it just delivers them
        # as soon as they are available (useful here, because we want to report the progress of the web search and
        # scraping as soon as things are done, instead of adhering to the order in which the promises were "registered"
        # to be part of the response sequence).
        ctx.reply_out_of_order(search_and_scraping_results)

        # Send the (promises of) web search and scraping results to the final answer agent too.
        # NOTE: We could use `send_out_of_order` instead of `send_message` here as well, but we don't really care one
        # way or another - the `final_answer_agent` is designed to start its work only after all its input is available
        # (all the incoming promises are resolved) anyway.
        final_answer_call.send_message(search_and_scraping_results)

    # Again, no `await` below. We are still exchanging promises. The agents that were called will start their work in
    # the background as soon as task switching happens.
    #
    # By default, `reply_sequence`, apart from returning a promise of a sequence (of promises of messages, to be
    # technically precise), also closes the call that was started with `initiate_call`. In other words, it "informs"
    # the agent that is being called that there will be no more input. We could change this behavior by adding the
    # following parameter if it was necessary: `.reply_sequence(finish_call=False)`
    ctx.reply(final_answer_call.reply_sequence())


@miniagent
async def web_search_agent(
    ctx: InteractionContext,
    search_query: str,
    rationale: str,
    already_picked_urls: set[str],
) -> None:
    ctx.reply(f'SEARCHING FOR "{search_query}"\n{rationale}')

    try:
        # Execute the search query
        search_results = await fetch_google_search(search_query)
    except Exception:  # pylint: disable=broad-exception-caught
        # Something went wrong upon the first attempt - let's give Bright Data SERP API a second chance...
        await asyncio.sleep(SLEEP_BEFORE_RETRY_SEC)
        ctx.reply(f"RETRYING SEARCH: {search_query}")
        search_results = await fetch_google_search(search_query)

    ctx.reply(f"SEARCH SUCCESSFUL: {search_query}")

    # Analyze search results to identify relevant web pages
    message_dicts = await aprepare_dicts_for_openai(
        [
            ctx.message_promises,
            f"RATIONALE: {rationale}\n\nSEARCH QUERY: {search_query}\n\nSEARCH RESULTS:\n\n{search_results}",
        ],
        system=(
            "This is a user question that another AI agent (not you) will have to answer. Your job, however, is to "
            "list all the web page urls that need to be inspected to collect information related to the "
            "RATIONALE and SEARCH QUERY. SEARCH RESULTS where to take the page urls from are be provided to you as "
            "well. Current date is " + datetime.now().strftime("%Y-%m-%d")
        ),
    )
    # No built-in miniagent for OpenAI's Structured Output feature (yet), so we will use OpenAI's client directly
    response = await openai_client.beta.chat.completions.parse(
        model=SMARTER_MODEL,
        messages=message_dicts,
        response_format=WebPagesToBeRead,  # See the definition of this class at the bottom of this file
    )
    parsed: WebPagesToBeRead = response.choices[0].message.parsed

    # Filter out pages that were already picked for scraping and also limit the number of pages to be scraped
    web_pages_to_scrape: list[WebPage] = []
    for web_page in parsed.web_pages:
        if web_page.url not in already_picked_urls:
            web_pages_to_scrape.append(web_page)
            already_picked_urls.add(web_page.url)
        if len(web_pages_to_scrape) >= MAX_WEB_PAGES_PER_SEARCH:
            break

    # Trigger scraping for each identified web page (no `await` in front of `trigger`, so again, read this as "schedule
    # for parallel execution")
    for web_page in web_pages_to_scrape:
        # Return scraping results in order of their availability rather than sequentially (`reply_out_of_order`, see
        # more detailed explanation earlier in this file)
        ctx.reply_out_of_order(
            page_scraper_agent.trigger(
                ctx.message_promises,
                url=web_page.url,
                rationale=web_page.rationale,
            )
        )


@miniagent
async def page_scraper_agent(
    ctx: InteractionContext,
    url: str,
    rationale: str,
) -> None:
    ctx.reply(f"READING PAGE: {url}\n{rationale}")

    try:
        # Scrape the web page
        page_content = await scrape_web_page(url)
    except Exception:  # pylint: disable=broad-exception-caught
        # Something went wrong upon the first attempt - let's give Bright Data Scraping Browser a second chance...
        await asyncio.sleep(SLEEP_BEFORE_RETRY_SEC)
        ctx.reply(f"RETRYING: {url}")
        page_content = await scrape_web_page(url)

    # Extract relevant information from the scraped web page.
    # NOTE: This time we ARE awaiting for the completed OpenAI response instead of accepting a sequence promise. This
    # is because we want to make sure that the page summary was generated without any problems before we report
    # success.
    page_summary = await OpenAIAgent.trigger(
        # `OpenAIAgent` is a built-in miniagent for text generation using OpenAI
        [
            ctx.message_promises,
            f"URL: {url}\nRATIONALE: {rationale}\n\nWEB PAGE CONTENT:\n\n{page_content}",
        ],
        system=(
            "This is a user question that another AI agent (not you) will have to answer. Your job, however, is "
            "to extract from WEB PAGE CONTENT facts that are relevant to the users original "
            "question. The other AI agent will use the information you extract along with information extracted "
            "by other agents to answer the user's original question later. "
            "Current date is " + datetime.now().strftime("%Y-%m-%d")
        ),
        model=MODEL,
        # Streaming doesn't really matter for internal use, could be False, could be True
        stream=False,
        # Let's break the flow of the current agent if LLM completion goes wrong (you will see at the very end of this
        # file that we set `errors_as_messages` to True globally for all agents)
        errors_as_messages=False,
        response_metadata={
            # This message, apart from being forwarded by the `research_agent` to the `final_answer_agent`, will also
            # be delivered all the way to the user, so let's prevent it from being displayed (unless we wanted the user
            # to see the internal "thinking" process of this agentic system with all its details).
            # NOTE: We came up with the "not_for_user" attribute name specifically in this app. We could have used any
            # other name, as long as we properly read it back (see the `main` function at the top of this file).
            "not_for_user": True,
        },
    )
    ctx.reply(f"SCRAPING SUCCESSFUL: {url}")  # Let's report success
    ctx.reply(page_summary)  # and send the summary


@miniagent
async def final_answer_agent(ctx: InteractionContext, user_question: Union[Message, tuple[Message, ...]]) -> None:
    # Here we await for the incoming `MessageSequencePromise` to materialize into a tuple of concrete `Message` objects
    # (which would be the result of this `await` if we assigned it to a variable) - as you remember, all the results of
    # the web searching and scraping are sent as input to the `final_answer_agent` (see the `research_agent` above).
    await ctx.message_promises
    # The only reason we do this `await` here is because we do not want the "=== ANSWER: ===" message below (which is
    # available immediately, because it is a concrete string) to be sent to the user earlier than all the web searching
    # and scraping is done.
    #
    # As you might remember, the reports of the searching and scraping progress are being returned to the user as "out
    # of order" messages. Such messages are allowed to be delivered both, earlier as well as later than the "ordered"
    # messages in the response sequence of an agent, depending on the timing of their availability.
    ctx.reply("==========\nANSWER:\n==========")

    # Just to be clear. It's not the answer that is generated by OpenAI miniagent (below) that requires you to
    # explicitly `await` for incoming messages, it is only the "=== ANSWER: ===" part (above) that does. We don't want
    # the user to see the "=== ANSWER: ===" text first and then start receiving "SEARCHING", "READING PAGE",
    # "SCRAPING SUCCESSFUL" etc.
    #
    # Since the generation of the final answer using OpenAI expects all the incoming messages to become part of the
    # prompt (the `ctx.message_promises` part of the `trigger` parameters below), it would only have started after
    # everything else was done regardless of whether you awaited for input explicitly or not.
    ctx.reply(
        # `OpenAIAgent` is a built-in miniagent for text generation using OpenAI
        OpenAIAgent.trigger(
            [
                "USER QUESTION:",
                user_question,
                "INFORMATION FOUND ON THE INTERNET:",
                # The `as_single_text_promise()` method concatenates all the messages in the promised sequence into a
                # single text message promise with the original messages separated by double newlines. As you can see,
                # it also returns a promise (and there is no `await` in front of it). The actual concatenation happens
                # in the background because the messages that are being concatenated might also not be available right
                # away.
                ctx.message_promises.as_single_text_promise(),
            ],
            system=(
                "Please answer the USER QUESTION based on the INFORMATION FOUND ON THE INTERNET. "
                "Current date is " + datetime.now().strftime("%Y-%m-%d")
            ),
            model=MODEL,
        )
    )


class WebSearch(BaseModel):
    rationale: str
    web_search_query: str


class WebSearchesToBeDone(BaseModel):
    web_searches: tuple[WebSearch, ...]


class WebPage(BaseModel):
    rationale: str
    url: str


class WebPagesToBeRead(BaseModel):
    web_pages: tuple[WebPage, ...]


if __name__ == "__main__":
    MiniAgents(
        # # Make OpenAIAgent (as well as any other LLM miniagent) log LLM requests and responses as markdown files in
        # # the `llm_logs` folder under the current working directory (helps understand what happens under the hood).
        # # Check the `llm_logs` folder after you run this app to see what those files looks like.
        llm_logger_agent=True,
        # # Let's make the system as robust as possible by not failing any of the agents upon errors (circle those
        # # errors around as part of agent communications instead - the language model will know to ignore them and
        # # will attempt to answer based on whatever information is available)
        errors_as_messages=True,
        # # When we set `errors_as_messages` to True, the tracebacks are not included into the message content by
        # # default, only the class names and the error message strings are. If you need to see tracebacks to
        # # troubleshoot errors, uncomment the line below.
        # error_tracebacks_in_messages=True,
    ).run(main())
