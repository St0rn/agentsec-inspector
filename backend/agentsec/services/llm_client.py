from __future__ import annotations

import asyncio
import copy
import os
import re
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


_PATH_PART = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


def _path_parts(path: str, *, label: str) -> list[str]:
    parts = path.split(".") if path else []
    if not 1 <= len(parts) <= 12 or any(not _PATH_PART.fullmatch(part) for part in parts):
        raise ValueError(f"Invalid {label}; use 1 to 12 dot-separated JSON field names")
    return parts


def _set_json_path(payload: dict[str, Any], path: str, value: Any, *, label: str) -> None:
    parts = _path_parts(path, label=label)
    current = payload
    for part in parts[:-1]:
        child = current.setdefault(part, {})
        if not isinstance(child, dict):
            raise ValueError(f"{label} conflicts with static_payload at {part!r}")
        current = child
    current[parts[-1]] = value


def _get_json_path(payload: Any, path: str, *, label: str) -> Any:
    current = payload
    for part in _path_parts(path, label=label):
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            raise RuntimeError(f"Chatbot response does not contain configured path {path!r}")
    return current


async def send_chat(
    target: Target, messages: list[dict[str, str]], max_tokens: int, settings: Settings
) -> LLMResult:
    config = target.configuration
    endpoint = target.endpoint or ""
    endpoint = validate_outbound_url(
        endpoint, remote_authorized=target.remote_authorized, settings=settings
    )
    headers = {"Content-Type": "application/json"}
    configured_headers = config.get("headers", {})
    if configured_headers:
        if not isinstance(configured_headers, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in configured_headers.items()
        ):
            raise ValueError("Configured chatbot headers must be a string-to-string object")
        blocked_headers = {
            "authorization",
            "proxy-authorization",
            "cookie",
            "host",
            "content-length",
            "transfer-encoding",
            "connection",
        }
        if any(
            not re.fullmatch(r"[A-Za-z0-9-]{1,100}", key)
            or key.casefold() in blocked_headers
            or "\r" in value
            or "\n" in value
            or len(value) > 4096
            for key, value in configured_headers.items()
        ):
            raise ValueError(
                "Configured chatbot headers contain a forbidden name or invalid value"
            )
        headers.update(configured_headers)
    key_env = str(config.get("api_key_env", ""))
    if key_env:
        token = os.getenv(key_env)
        if not token:
            raise RuntimeError(
                f"Configured credential environment variable {key_env!r} is unavailable"
            )
        key_header = str(config.get("api_key_header", "Authorization"))
        if not re.fullmatch(r"[A-Za-z0-9-]{1,100}", key_header):
            raise ValueError("Invalid API key header name")
        key_prefix = str(config.get("api_key_prefix", "Bearer"))
        if "\r" in key_prefix or "\n" in key_prefix or len(key_prefix) > 100:
            raise ValueError("Invalid API key prefix")
        headers[key_header] = f"{key_prefix} {token}".strip()
    model = str(config.get("model", ""))
    if target.target_type == "ollama":
        url = endpoint.rstrip("/") + "/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
    elif target.target_type == "chatbot":
        url = endpoint.rstrip("/")
        static_payload = config.get("static_payload", {})
        if not isinstance(static_payload, dict):
            raise ValueError("chatbot static_payload must be a JSON object")
        payload = copy.deepcopy(static_payload)
        message_path = str(config.get("message_path", "message"))
        _set_json_path(payload, message_path, messages[-1]["content"], label="message_path")
        history_path = str(config.get("history_path", ""))
        if history_path:
            _set_json_path(payload, history_path, messages, label="history_path")
        max_tokens_path = str(config.get("max_tokens_path", ""))
        if max_tokens_path:
            _set_json_path(payload, max_tokens_path, max_tokens, label="max_tokens_path")
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
    if not isinstance(raw, dict):
        raise RuntimeError("LLM endpoint returned a non-object JSON response")
    if target.target_type == "ollama":
        message = raw.get("message", {})
    elif target.target_type == "chatbot":
        content = _get_json_path(
            raw, str(config.get("response_path", "response")), label="response_path"
        )
        tool_calls_path = str(config.get("tool_calls_path", ""))
        tool_calls = (
            _get_json_path(raw, tool_calls_path, label="tool_calls_path")
            if tool_calls_path
            else []
        )
        if not isinstance(content, str):
            raise RuntimeError("Configured chatbot response path does not contain text")
        if not isinstance(tool_calls, list):
            raise RuntimeError("Configured chatbot tool-calls path does not contain a list")
        return LLMResult(content, raw, tool_calls)
    else:
        choices = raw.get("choices", [])
        if not choices:
            raise RuntimeError("LLM endpoint returned no choices")
        message = choices[0].get("message", {})
    return LLMResult(str(message.get("content") or ""), raw, message.get("tool_calls") or [])
