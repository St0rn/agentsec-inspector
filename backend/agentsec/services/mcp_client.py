from __future__ import annotations

import asyncio
import json
import os
import shutil
from dataclasses import dataclass
from typing import Any

import httpx

from ..config import Settings
from ..security import TargetSecurityError, validate_outbound_url


class MCPProtocolError(RuntimeError):
    pass


@dataclass
class MCPDiscovery:
    server_info: dict[str, Any]
    capabilities: dict[str, Any]
    tools: list[dict[str, Any]]
    resources: list[dict[str, Any]]
    prompts: list[dict[str, Any]]


def _decode_response(text: str, content_type: str) -> dict[str, Any]:
    if "text/event-stream" in content_type:
        for line in text.splitlines():
            if line.startswith("data:"):
                payload = line[5:].strip()
                if payload and payload != "[DONE]":
                    value = json.loads(payload)
                    if isinstance(value, dict) and ("result" in value or "error" in value):
                        return value
        raise MCPProtocolError("No JSON-RPC result in the MCP event stream")
    value = json.loads(text)
    if not isinstance(value, dict):
        raise MCPProtocolError("MCP response is not a JSON-RPC object")
    return value



async def _collect_mcp_pages(
    call: Any, method: str, field: str, *, max_pages: int | None = None
) -> list[dict[str, Any]]:
    """Retrieve every advertised page, with cycle and resource limits.

    The MCP list methods use cursor/nextCursor. Never treat the first response
    as a complete inventory when the server supplies nextCursor.
    """
    if max_pages is None:
        try:
            max_pages = int(os.getenv("AGENTSEC_MCP_MAX_PAGES", "50"))
        except ValueError as exc:
            raise MCPProtocolError("AGENTSEC_MCP_MAX_PAGES must be an integer") from exc
    max_pages = max(1, min(max_pages, 200))
    cursor: str | None = None
    seen: set[str] = set()
    collected: list[dict[str, Any]] = []
    for _ in range(max_pages):
        result = await call(method, {"cursor": cursor} if cursor is not None else None)
        page = result.get(field, [])
        if not isinstance(page, list) or any(not isinstance(item, dict) for item in page):
            raise MCPProtocolError(f"{method} returned an invalid {field} list")
        collected.extend(page)
        next_cursor = result.get("nextCursor")
        if next_cursor is None or next_cursor == "":
            return collected
        if not isinstance(next_cursor, str) or next_cursor in seen:
            raise MCPProtocolError(f"{method} returned an invalid or repeated nextCursor")
        seen.add(next_cursor)
        cursor = next_cursor
    raise MCPProtocolError(
        f"{method} exceeded {max_pages} pages; raise AGENTSEC_MCP_MAX_PAGES explicitly"
    )

class HTTPMCPClient:
    def __init__(
        self, endpoint: str, headers: dict[str, str], settings: Settings, remote_authorized: bool
    ):
        self.endpoint = validate_outbound_url(
            endpoint, remote_authorized=remote_authorized, settings=settings
        )
        self.headers = {
            k: v for k, v in headers.items() if k.lower() not in {"host", "content-length"}
        }
        self.headers.update(
            {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
        )
        self.timeout = settings.request_timeout_seconds
        self.max_bytes = settings.max_response_bytes
        self.session_id: str | None = None
        self._counter = 0

    async def call(
        self, method: str, params: dict[str, Any] | None = None, notification: bool = False
    ) -> dict[str, Any]:
        self._counter += 1
        request: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            request["params"] = params
        if not notification:
            request["id"] = self._counter
        headers = dict(self.headers)
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
            response = await client.post(self.endpoint, headers=headers, json=request)
        if response.status_code >= 400:
            raise MCPProtocolError(f"MCP HTTP status {response.status_code}")
        if len(response.content) > self.max_bytes:
            raise MCPProtocolError("MCP response exceeded the configured size limit")
        self.session_id = response.headers.get("mcp-session-id", self.session_id)
        if notification or not response.content:
            return {}
        result = _decode_response(response.text, response.headers.get("content-type", ""))
        if "error" in result:
            raise MCPProtocolError(f"MCP error: {result['error']}")
        return result.get("result", {})

    async def discover(self) -> MCPDiscovery:
        initialized = await self.call(
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "AgentSec Inspector", "version": "1.2.0"},
            },
        )
        await self.call("notifications/initialized", notification=True)
        capabilities = initialized.get("capabilities", {})
        tools = await _collect_mcp_pages(self.call, "tools/list", "tools") if "tools" in capabilities else []
        resources = (
            await _collect_mcp_pages(self.call, "resources/list", "resources")
            if "resources" in capabilities else []
        )
        prompts = (
            await _collect_mcp_pages(self.call, "prompts/list", "prompts")
            if "prompts" in capabilities else []
        )
        return MCPDiscovery(
            initialized.get("serverInfo", {}), capabilities, tools, resources, prompts
        )

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return await self.call("tools/call", {"name": name, "arguments": arguments})


class StdioMCPClient:
    def __init__(self, command: str, args: list[str], settings: Settings):
        allowlist = {
            item.strip()
            for item in os.getenv("AGENTSEC_ALLOWED_MCP_EXECUTABLES", "").split(",")
            if item.strip()
        }
        resolved = shutil.which(command)
        if not resolved or (command not in allowlist and resolved not in allowlist):
            raise TargetSecurityError(
                "MCP executable is not allowed. Add its exact name or resolved path to AGENTSEC_ALLOWED_MCP_EXECUTABLES."
            )
        if len(args) > 64 or any(len(item) > 4096 or "\x00" in item for item in args):
            raise TargetSecurityError("Invalid MCP process arguments")
        self.command = resolved
        self.args = args
        self.timeout = settings.request_timeout_seconds
        self.process: asyncio.subprocess.Process | None = None
        self._counter = 0

    async def __aenter__(self) -> StdioMCPClient:
        env = {"PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}
        self.process = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            limit=2_000_000,
        )
        return self

    async def __aexit__(self, *_args: object) -> None:
        if self.process and self.process.returncode is None:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=3)
            except TimeoutError:
                self.process.kill()
                await self.process.wait()

    async def call(
        self, method: str, params: dict[str, Any] | None = None, notification: bool = False
    ) -> dict[str, Any]:
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise MCPProtocolError("MCP process is not running")
        self._counter += 1
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        if not notification:
            payload["id"] = self._counter
        self.process.stdin.write(json.dumps(payload, separators=(",", ":")).encode() + b"\n")
        await self.process.stdin.drain()
        if notification:
            return {}
        line = await asyncio.wait_for(self.process.stdout.readline(), self.timeout)
        if not line:
            raise MCPProtocolError("MCP process closed its output")
        response = json.loads(line)
        if response.get("error"):
            raise MCPProtocolError(f"MCP error: {response['error']}")
        return response.get("result", {})

    async def discover(self) -> MCPDiscovery:
        initialized = await self.call(
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "AgentSec Inspector", "version": "1.2.0"},
            },
        )
        await self.call("notifications/initialized", notification=True)
        capabilities = initialized.get("capabilities", {})
        tools = await _collect_mcp_pages(self.call, "tools/list", "tools") if "tools" in capabilities else []
        resources = (
            await _collect_mcp_pages(self.call, "resources/list", "resources")
            if "resources" in capabilities else []
        )
        prompts = (
            await _collect_mcp_pages(self.call, "prompts/list", "prompts")
            if "prompts" in capabilities else []
        )
        return MCPDiscovery(
            initialized.get("serverInfo", {}), capabilities, tools, resources, prompts
        )

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return await self.call("tools/call", {"name": name, "arguments": arguments})
