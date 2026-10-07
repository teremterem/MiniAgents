# Parallel Search MCP with MiniAgents

This example wraps Parallel's `web_search` and `web_fetch` MCP tools in custom
MiniAgents. It prints structured results with source URLs and excerpts, suitable
for passing to another agent. It does not generate a synthesized answer or use
an LLM.

The [anonymous Search MCP endpoint](https://docs.parallel.ai/integrations/mcp/search-mcp)
is free for exploration and light use, with rate limits. No Parallel account,
API key, or model credentials are needed. The example uses Streamable HTTP at
`https://search.parallel.ai/mcp` and sends `MiniAgents/parallel-search-example` as
its User-Agent. It does not load credentials from your environment or `.env`.

## Install

The MCP SDK requires Python 3.10 or newer. From this directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Search with an objective and optional related keyword queries:

```bash
python parallel_search.py "Find MiniAgents documentation and examples" \
  --query "MiniAgents Python framework documentation"
```

Fetch excerpts from a URL, for example one returned by a search:

```bash
python parallel_search.py --url https://github.com/teremterem/MiniAgents
```

Repeat `--query` or `--url` for multiple queries or pages. An objective and URLs
can also be supplied together; search runs first, then fetch. They share one MCP
session and tool session identifier. Fetch uses explicit URLs rather than
selecting pages automatically. Fetch results retain per-URL errors, and MCP tool
errors propagate through the MiniAgents reply promises. Requests and tool replies
have 60-second timeouts; rate-limit failures are surfaced without automatic retries.

To reuse the agents, fork with `non_freezable_kwargs={"session": session}` and
`session_id=...` as in `main()`, then consume their reply promises while the MCP
session remains open. In an application using an LLM, model inference and its
credentials are separate from anonymous search access.
