from __future__ import annotations

import pytest

from agentsec.services.mcp_analysis import analyse_discovery, is_sensitive_tool
from agentsec.services.mcp_client import MCPProtocolError, _collect_mcp_pages


@pytest.mark.asyncio
async def test_paginated_mcp_discovery_collects_all_pages() -> None:
    seen: list[tuple[str, dict[str, str] | None]] = []

    async def call(method: str, params: dict[str, str] | None = None) -> dict:
        seen.append((method, params))
        if not params:
            return {"resources": [{"uri": "mcp://first"}], "nextCursor": "page-2"}
        return {"resources": [{"uri": "mcp://second"}]}

    resources = await _collect_mcp_pages(call, "resources/list", "resources")
    assert [item["uri"] for item in resources] == ["mcp://first", "mcp://second"]
    assert seen == [
        ("resources/list", None),
        ("resources/list", {"cursor": "page-2"}),
    ]


@pytest.mark.asyncio
async def test_paginated_mcp_discovery_rejects_cycles_and_page_overflow() -> None:
    async def cycle(_method: str, _params: dict | None = None) -> dict:
        return {"tools": [{"name": "read_note"}], "nextCursor": "same"}

    with pytest.raises(MCPProtocolError, match="repeated nextCursor"):
        await _collect_mcp_pages(cycle, "tools/list", "tools")

    async def unbounded(_method: str, params: dict | None = None) -> dict:
        return {"prompts": [], "nextCursor": str(int(params["cursor"]) + 1) if params else "1"}

    with pytest.raises(MCPProtocolError, match="exceeded 2 pages"):
        await _collect_mcp_pages(unbounded, "prompts/list", "prompts", max_pages=2)


@pytest.mark.asyncio
async def test_paginated_mcp_discovery_rejects_malformed_items() -> None:
    async def malformed(_method: str, _params: dict | None = None) -> dict:
        return {"resources": [None, "invalid"]}

    with pytest.raises(MCPProtocolError, match="invalid resources list"):
        await _collect_mcp_pages(malformed, "resources/list", "resources")


def test_sondahub_read_only_descriptions_not_rated_sensitive() -> None:
    innocent = [
        {
            "name": "whoami",
            "description": "Identity and scopes in your access token",
            "annotations": {"readOnlyHint": True, "destructiveHint": False},
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "slow_operation",
            "description": "Sends progressToken notifications for a long request",
            "annotations": {"readOnlyHint": True, "destructiveHint": False},
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    ]
    assert all(not is_sensitive_tool(tool) for tool in innocent)
    assert analyse_discovery({"tools": innocent}) == []


def test_explicitly_mutating_tool_always_requires_confirmation() -> None:
    assert is_sensitive_tool(
        {
            "name": "delete_record",
            "description": "Delete a record",
            "annotations": {"readOnlyHint": True, "destructiveHint": False},
        }
    )
    assert is_sensitive_tool(
        {
            "name": "manage_record",
            "description": "Administrative delete operation",
            "annotations": {"readOnlyHint": True},
        }
    )
    assert is_sensitive_tool(
        {
            "name": "mutate",
            "description": "Takes action",
            "annotations": {"readOnlyHint": False},
        }
    )
    assert not is_sensitive_tool("add")
