from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx
import pytest

from agentsec.config import Settings
from agentsec.models import Target
from agentsec.security import TargetSecurityError
from agentsec.services import llm_client, mcp_client
from agentsec.services.mcp_client import HTTPMCPClient, MCPProtocolError, StdioMCPClient

REAL_ASYNC_CLIENT = httpx.AsyncClient


class AsyncHTTPFixture:
    responder: Callable[[str, dict[str, str], dict[str, Any]], httpx.Response]

    def __init__(self, *_args: object, **_kwargs: object):
        pass

    async def __aenter__(self) -> AsyncHTTPFixture:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def post(
        self, url: str, *, headers: dict[str, str], json: dict[str, Any]
    ) -> httpx.Response:
        return self.responder(url, headers, json)


def response(status: int, payload: dict[str, Any], **headers: str) -> httpx.Response:
    return httpx.Response(
        status,
        json=payload,
        headers=headers,
        request=httpx.Request("POST", "http://127.0.0.1:9999/mcp"),
    )


@pytest.mark.asyncio
async def test_http_mcp_discovery_and_active_call(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    observed: list[tuple[str, str | None]] = []

    def responder(_url: str, headers: dict[str, str], body: dict[str, Any]) -> httpx.Response:
        observed.append((body["method"], headers.get("Mcp-Session-Id")))
        method = body["method"]
        results = {
            "initialize": {
                "serverInfo": {"name": "fixture"},
                "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
            },
            "tools/list": {"tools": [{"name": "read_note", "inputSchema": {}}]},
            "resources/list": {"resources": [{"uri": "fixture://policy"}]},
            "prompts/list": {"prompts": [{"name": "summary"}]},
            "tools/call": {"content": [{"type": "text", "text": "ok"}], "isError": False},
        }
        if method == "notifications/initialized":
            return httpx.Response(202, request=httpx.Request("POST", _url))
        return response(
            200,
            {"jsonrpc": "2.0", "id": body.get("id"), "result": results[method]},
            **({"mcp-session-id": "fixture-session"} if method == "initialize" else {}),
        )

    AsyncHTTPFixture.responder = staticmethod(responder)
    monkeypatch.setattr(mcp_client.httpx, "AsyncClient", AsyncHTTPFixture)
    client = HTTPMCPClient("http://127.0.0.1:9999/mcp", {}, Settings(data_dir=tmp_path), False)
    discovery = await client.discover()
    result = await client.call_tool("read_note", {})
    assert discovery.server_info["name"] == "fixture"
    assert len(discovery.tools) == len(discovery.resources) == len(discovery.prompts) == 1
    assert result["isError"] is False
    assert observed[0] == ("initialize", None)
    assert all(session == "fixture-session" for _, session in observed[1:])


@pytest.mark.asyncio
async def test_http_mcp_errors_and_response_limits(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    def forbidden(_url: str, _headers: dict[str, str], _body: dict[str, Any]) -> httpx.Response:
        return response(403, {"error": "forbidden"})

    AsyncHTTPFixture.responder = staticmethod(forbidden)
    monkeypatch.setattr(mcp_client.httpx, "AsyncClient", AsyncHTTPFixture)
    client = HTTPMCPClient("http://127.0.0.1:9999/mcp", {}, Settings(data_dir=tmp_path), False)
    with pytest.raises(MCPProtocolError, match="status 403"):
        await client.call("tools/list")

    def rpc_error(_url: str, _headers: dict[str, str], body: dict[str, Any]) -> httpx.Response:
        return response(200, {"jsonrpc": "2.0", "id": body["id"], "error": {"code": -1}})

    AsyncHTTPFixture.responder = staticmethod(rpc_error)
    with pytest.raises(MCPProtocolError, match="MCP error"):
        await client.call("tools/list")

    def oversized(_url: str, _headers: dict[str, str], body: dict[str, Any]) -> httpx.Response:
        return response(200, {"jsonrpc": "2.0", "id": body["id"], "result": {"data": "x" * 100}})

    AsyncHTTPFixture.responder = staticmethod(oversized)
    client.max_bytes = 10
    with pytest.raises(MCPProtocolError, match="size limit"):
        await client.call("tools/list")


def test_stdio_mcp_requires_exact_executable_allowlist(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.setattr(mcp_client.shutil, "which", lambda _command: "/opt/lab/mcp-server")
    monkeypatch.delenv("AGENTSEC_ALLOWED_MCP_EXECUTABLES", raising=False)
    with pytest.raises(TargetSecurityError, match="not allowed"):
        StdioMCPClient("mcp-server", [], Settings(data_dir=tmp_path))
    monkeypatch.setenv("AGENTSEC_ALLOWED_MCP_EXECUTABLES", "/opt/lab/mcp-server")
    client = StdioMCPClient("mcp-server", ["--safe"], Settings(data_dir=tmp_path))
    assert client.command == "/opt/lab/mcp-server"
    with pytest.raises(TargetSecurityError, match="Invalid MCP process arguments"):
        StdioMCPClient("mcp-server", ["x"] * 65, Settings(data_dir=tmp_path))


def llm_target(target_type: str = "openai", configuration: dict[str, Any] | None = None) -> Target:
    return Target(
        project_id="project",
        name="fixture",
        target_type=target_type,
        endpoint="http://127.0.0.1:9999",
        configuration=configuration or {"model": "fixture-model", "retries": 0},
        remote_authorized=False,
    )


@pytest.mark.asyncio
async def test_openai_compatible_and_ollama_clients(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    bodies: list[dict[str, Any]] = []

    def responder(url: str, _headers: dict[str, str], body: dict[str, Any]) -> httpx.Response:
        bodies.append(body)
        if url.endswith("/api/chat"):
            payload = {"message": {"content": "ollama response"}}
        else:
            payload = {
                "choices": [
                    {
                        "message": {
                            "content": "compatible response",
                            "tool_calls": [{"id": "call-1"}],
                        }
                    }
                ]
            }
        return response(200, payload)

    AsyncHTTPFixture.responder = staticmethod(responder)
    monkeypatch.setattr(llm_client.httpx, "AsyncClient", AsyncHTTPFixture)
    settings = Settings(data_dir=tmp_path)
    compatible = await llm_client.send_chat(
        llm_target(), [{"role": "user", "content": "test"}], 100, settings
    )
    ollama = await llm_client.send_chat(
        llm_target("ollama"), [{"role": "user", "content": "test"}], 100, settings
    )
    assert compatible.text == "compatible response" and compatible.tool_calls
    assert ollama.text == "ollama response"
    assert bodies[0]["temperature"] == 0
    assert bodies[1]["stream"] is False


@pytest.mark.asyncio
async def test_generic_chatbot_maps_nested_request_response_and_authentication(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    observed: dict[str, Any] = {}

    def responder(url: str, headers: dict[str, str], body: dict[str, Any]) -> httpx.Response:
        observed.update(url=url, headers=headers, body=body)
        return response(
            200,
            {
                "answer": {"text": "The fictional marker remains protected."},
                "actions": [{"name": "search", "blocked": True}],
            },
        )

    AsyncHTTPFixture.responder = staticmethod(responder)
    monkeypatch.setattr(llm_client.httpx, "AsyncClient", AsyncHTTPFixture)
    monkeypatch.setenv("CHATBOT_TEST_KEY", "controlled-test-key")
    target = llm_target(
        "chatbot",
        {
            "message_path": "input.message",
            "history_path": "input.history",
            "max_tokens_path": "generation.limit",
            "response_path": "answer.text",
            "tool_calls_path": "actions",
            "static_payload": {"tenant": "authorised-lab"},
            "api_key_env": "CHATBOT_TEST_KEY",
            "api_key_header": "X-API-Key",
            "api_key_prefix": "",
            "retries": 0,
        },
    )
    target.endpoint = "https://127.0.0.1:9999/conversation"
    messages = [
        {"role": "system", "content": "Protect the marker."},
        {"role": "user", "content": "Run the controlled test."},
    ]
    result = await llm_client.send_chat(target, messages, 321, Settings(data_dir=tmp_path))
    assert observed["url"] == "https://127.0.0.1:9999/conversation"
    assert observed["headers"]["X-API-Key"] == "controlled-test-key"
    assert observed["body"] == {
        "tenant": "authorised-lab",
        "input": {"message": "Run the controlled test.", "history": messages},
        "generation": {"limit": 321},
    }
    assert result.text == "The fictional marker remains protected."
    assert result.tool_calls == [{"name": "search", "blocked": True}]


@pytest.mark.asyncio
async def test_generic_chatbot_rejects_transport_header_overrides(tmp_path) -> None:
    target = llm_target(
        "chatbot",
        {"headers": {"Host": "attacker.invalid"}, "response_path": "answer"},
    )
    with pytest.raises(ValueError, match="forbidden name"):
        await llm_client.send_chat(
            target,
            [{"role": "user", "content": "controlled test"}],
            20,
            Settings(data_dir=tmp_path),
        )


@pytest.mark.asyncio
async def test_llm_client_does_not_retry_post_after_transient_status(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    attempts = 0

    def responder(_url: str, _headers: dict[str, str], _body: dict[str, Any]) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return response(503, {"detail": "retry"})

    AsyncHTTPFixture.responder = staticmethod(responder)
    monkeypatch.setattr(llm_client.httpx, "AsyncClient", AsyncHTTPFixture)
    target = llm_target(configuration={"model": "fixture", "retries": 1})
    with pytest.raises(httpx.HTTPStatusError):
        await llm_client.send_chat(
            target, [{"role": "user", "content": "test"}], 20, Settings(data_dir=tmp_path)
        )
    assert attempts == 1


@pytest.mark.asyncio
async def test_llm_client_never_reads_missing_credential_as_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.delenv("AGENTSEC_MISSING_TEST_KEY", raising=False)
    target = llm_target(
        configuration={"model": "fixture", "api_key_env": "AGENTSEC_MISSING_TEST_KEY"}
    )
    with pytest.raises(RuntimeError, match="unavailable"):
        await llm_client.send_chat(
            target, [{"role": "user", "content": "test"}], 20, Settings(data_dir=tmp_path)
        )


def ndjson_client(monkeypatch: pytest.MonkeyPatch, handler: Callable[[httpx.Request], httpx.Response]) -> None:
    def factory(*_args: object, **kwargs: object) -> httpx.AsyncClient:
        return REAL_ASYNC_CLIENT(transport=httpx.MockTransport(handler), timeout=kwargs.get("timeout"))

    monkeypatch.setattr(llm_client.httpx, "AsyncClient", factory)


@pytest.mark.asyncio
async def test_ndjson_stream_reconstructs_response_events_tools_and_completion(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    body = "\n".join(
        [
            '{"type":"status","message":"Connexion"}',
            '{"type":"tool","name":"list_accounts","status":"read","detail":""}',
            '{"type":"token","text":"Votre"}',
            '{"type":"token","text":" compte"}',
            '{"type":"done","response":"Votre compte","tools":[{"tool":"list_accounts","detail":"","result":{"objects":[]}}],"model":"qwen2.5:3b","completed":false,"continuations":0}',
        ]
    )
    ndjson_client(monkeypatch, lambda request: httpx.Response(200, content=body, headers={"content-type": "application/x-ndjson"}, request=request))
    target = llm_target("chatbot", {"message_path": "message", "response_format": "ndjson"})
    result = await llm_client.send_chat(target, [{"role": "user", "content": "test"}], 50, Settings(data_dir=tmp_path))
    assert result.text == "Votre compte"
    assert result.completed is False
    assert result.metadata["model"] == "qwen2.5:3b"
    assert result.metadata["token_response_comparison"] == "match"  # noqa: S105
    assert len(result.events) == 5
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0]["result"] == {"objects": []}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ('{"type":"token","text":"ok"}\nnot-json', "Invalid NDJSON at line 2"),
        ("", "ended without an event"),
    ],
)
async def test_ndjson_rejects_malformed_or_empty_stream(
    monkeypatch: pytest.MonkeyPatch, tmp_path, body: str, expected: str
) -> None:
    ndjson_client(monkeypatch, lambda request: httpx.Response(200, content=body, headers={"content-type": "application/x-ndjson"}, request=request))
    target = llm_target("chatbot", {"response_format": "ndjson"})
    with pytest.raises(llm_client.LLMProtocolError, match=expected):
        await llm_client.send_chat(target, [{"role": "user", "content": "test"}], 20, Settings(data_dir=tmp_path))


@pytest.mark.asyncio
async def test_ndjson_enforces_size_limit_and_propagates_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    large = '{"type":"token","text":"' + ("x" * 500) + '"}'
    ndjson_client(monkeypatch, lambda request: httpx.Response(200, content=large, headers={"content-type": "application/x-ndjson"}, request=request))
    target = llm_target("chatbot", {"response_format": "ndjson"})
    with pytest.raises(llm_client.LLMProtocolError, match="size limit"):
        await llm_client.send_chat(target, [{"role": "user", "content": "test"}], 20, Settings(data_dir=tmp_path, max_response_bytes=100))

    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("interrupted", request=request)

    ndjson_client(monkeypatch, timeout)
    with pytest.raises(httpx.ReadTimeout):
        await llm_client.send_chat(target, [{"role": "user", "content": "test"}], 20, Settings(data_dir=tmp_path))


@pytest.mark.asyncio
async def test_sse_reconstructs_openai_tokens_and_fragmented_tool_call(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    body = "\n\n".join(
        [
            'data: {"choices":[{"delta":{"content":"Safe "}}]}',
            'data: {"choices":[{"delta":{"content":"answer","tool_calls":[{"index":0,"id":"call-1","type":"function","function":{"name":"search","arguments":"{\\"q\\":"}}]}}]}',
            'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"\\"docs\\"}"}}]}}]}',
            "data: [DONE]",
        ]
    )
    ndjson_client(monkeypatch, lambda request: httpx.Response(200, content=body, headers={"content-type": "text/event-stream"}, request=request))
    target = llm_target("openai", {"model": "fixture", "response_format": "sse", "stream": True})
    result = await llm_client.send_chat(target, [{"role": "user", "content": "test"}], 20, Settings(data_dir=tmp_path))
    assert result.text == "Safe answer"
    assert result.tool_calls[0]["function"] == {"name": "search", "arguments": '{"q":"docs"}'}
