"""Exercise the example's MiniAgents caller over a local MCP HTTP fixture."""

import argparse
import json

import httpx
import pytest

from miniagents import MiniAgents

import parallel_search


@pytest.mark.parametrize("tool_error", [False, True])
async def test_agent_dispatch(monkeypatch, capsys, tool_error):
    """Observe real HTTP arguments, discovery, tool dispatch and error propagation."""
    requests = []
    client_class = httpx.AsyncClient

    def respond(request):
        assert str(request.url) == parallel_search.MCP_URL
        assert request.headers["User-Agent"] == parallel_search.USER_AGENT
        assert "authorization" not in request.headers
        if request.method != "POST":
            return httpx.Response(405)
        payload = json.loads(request.content)
        requests.append(payload)
        method = payload["method"]
        if "id" not in payload:
            return httpx.Response(202)
        if method == "initialize":
            result = {
                "protocolVersion": payload["params"]["protocolVersion"],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "test-mcp", "version": "1"},
            }
        elif method == "tools/list":
            result = {
                "tools": [{"name": name, "inputSchema": {"type": "object"}} for name in ("web_search", "web_fetch")]
            }
        else:
            assert method == "tools/call"
            name = payload["params"]["name"]
            result = {
                "content": [{"type": "text", "text": "tool failed" if tool_error else name + " source excerpt"}],
                "isError": tool_error,
            }
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": payload["id"], "result": result})

    def client_factory(**kwargs):
        assert kwargs["timeout"] == 60
        return client_class(transport=httpx.MockTransport(respond), **kwargs)

    monkeypatch.setattr(parallel_search.httpx, "AsyncClient", client_factory)
    args = argparse.Namespace(objective="Find docs", query=["MiniAgents docs"], url=["https://example.org"])
    async with MiniAgents():
        if tool_error:
            with pytest.raises(Exception) as caught:
                await parallel_search.main(args)
            error = caught.value
            while hasattr(error, "exceptions"):
                assert len(error.exceptions) == 1
                error = error.exceptions[0]
            assert isinstance(error, RuntimeError)
            assert str(error) == "web_search: tool failed"
        else:
            await parallel_search.main(args)
    calls = [item["params"] for item in requests if item["method"] == "tools/call"]
    assert calls[0]["name"] == "web_search"
    assert calls[0]["arguments"]["objective"] == "Find docs"
    assert calls[0]["arguments"]["search_queries"] == ["MiniAgents docs"]
    if not tool_error:
        assert calls[1]["name"] == "web_fetch"
        assert calls[1]["arguments"]["urls"] == ["https://example.org"]
        assert calls[0]["arguments"]["session_id"] == calls[1]["arguments"]["session_id"]
        output = capsys.readouterr().out
        assert "web_search source excerpt" in output
        assert "web_fetch source excerpt" in output
