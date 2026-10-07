"""Search and fetch through anonymous Parallel MCP tools wrapped as MiniAgents."""

import argparse
import json
from datetime import timedelta
from uuid import uuid4

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from miniagents import InteractionContext, MiniAgents, miniagent

MCP_URL = "https://search.parallel.ai/mcp"
USER_AGENT = "MiniAgents/parallel-search-example"


async def tool_reply(ctx: InteractionContext, session: ClientSession, name: str, arguments: dict) -> None:
    """Preserve structured results, including source URLs and fetch errors."""
    result = await session.call_tool(name, arguments)
    text = "\n".join(item.text for item in result.content if item.type == "text")
    if result.isError:
        raise RuntimeError(f"{name}: {text}")
    if result.structuredContent is not None:
        text = json.dumps(result.structuredContent, indent=2, ensure_ascii=False)
    ctx.reply(text)


@miniagent
async def search_agent(ctx: InteractionContext, session: ClientSession, session_id: str, queries: tuple) -> None:
    """Use the incoming message as the search objective."""
    objective = str(await ctx.message_promises.as_single_text_promise())
    await tool_reply(
        ctx, session, "web_search", {"objective": objective, "search_queries": list(queries), "session_id": session_id}
    )


@miniagent
async def fetch_agent(ctx: InteractionContext, session: ClientSession, session_id: str, urls: tuple) -> None:
    """Fetch excerpts from explicit URLs; retain partial failures in the reply."""
    await tool_reply(ctx, session, "web_fetch", {"urls": list(urls), "session_id": session_id})


async def main(args: argparse.Namespace) -> None:
    """Keep the HTTP client and MCP session alive until all agent replies resolve."""
    session_id = str(uuid4())
    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=60, follow_redirects=True) as client:
        async with streamable_http_client(MCP_URL, http_client=client) as (read, write, _):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=60)) as session:
                await session.initialize()
                tools = {tool.name for tool in (await session.list_tools()).tools}
                required = {"web_search"} if args.objective else set()
                if args.url:
                    required.add("web_fetch")
                if not required.issubset(tools):
                    raise RuntimeError(f"Missing MCP tools: {sorted(required - tools)}")
                # Sessions are mutable resources, so use non_freezable_kwargs when forking.
                agent_kwargs = {"non_freezable_kwargs": {"session": session}, "session_id": session_id}
                if args.objective:
                    replies = search_agent.fork(**agent_kwargs).trigger(
                        args.objective, queries=tuple(args.query or [args.objective])
                    )
                    async for reply in replies:
                        print(await reply)
                if args.url:
                    replies = fetch_agent.fork(**agent_kwargs).trigger(urls=tuple(args.url))
                    async for reply in replies:
                        print(await reply)


def parse_args() -> argparse.Namespace:
    """Accept a search objective, URLs to fetch, or both."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("objective", nargs="?", help="What you want to find")
    parser.add_argument("--query", action="append", help="Search keywords; repeat for related queries")
    parser.add_argument("--url", action="append", help="URL to fetch; repeat for multiple pages")
    args = parser.parse_args()
    if not args.objective and not args.url:
        parser.error("provide an objective or --url")
    if args.query and not args.objective:
        parser.error("--query requires an objective")
    return args


if __name__ == "__main__":
    MiniAgents().run(main(parse_args()))
