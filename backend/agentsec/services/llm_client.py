from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any

import httpx

from ..config import Settings
from ..models import Target
from ..security import validate_outbound_url


@dataclass
class LLMResult:
    text: str
    raw: dict[str, Any]
    tool_calls: list[dict[str, Any]]


async def send_chat(
    target: Target, messages: list[dict[str, str]], max_tokens: int, settings: Settings
) -> LLMResult:
    config = target.configuration
    endpoint = target.endpoint or ""
    endpoint = validate_outbound_url(
        endpoint, remote_authorized=target.remote_authorized, settings=settings
    )
    headers = {"Content-Type": "application/json"}
    key_env = str(config.get("api_key_env", ""))
    if key_env:
        token = os.getenv(key_env)
        if not token:
            raise RuntimeError(
                f"Configured credential environment variable {key_env!r} is unavailable"
            )
        headers["Authorization"] = f"Bearer {token}"
    model = str(config.get("model", ""))
    if target.target_type == "ollama":
        url = endpoint.rstrip("/") + "/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
    else:
        url = endpoint.rstrip("/")
        if not url.endswith("/chat/completions"):
            url += "/v1/chat/completions"
        payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0}
    timeout = httpx.Timeout(settings.request_timeout_seconds)
    retries = min(max(int(config.get("retries", 1)), 0), 2)
    response: httpx.Response | None = None
    for attempt in range(retries + 1):
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            response = await client.post(url, headers=headers, json=payload)
        if response.status_code not in {429, 502, 503, 504} or attempt == retries:
            break
        await asyncio.sleep(0.25 * (2**attempt))
    assert response is not None
    response.raise_for_status()
    if len(response.content) > settings.max_response_bytes:
        raise RuntimeError("LLM response exceeded the configured size limit")
    raw = response.json()
    if target.target_type == "ollama":
        message = raw.get("message", {})
    else:
        choices = raw.get("choices", [])
        if not choices:
            raise RuntimeError("LLM endpoint returned no choices")
        message = choices[0].get("message", {})
    return LLMResult(str(message.get("content") or ""), raw, message.get("tool_calls") or [])
