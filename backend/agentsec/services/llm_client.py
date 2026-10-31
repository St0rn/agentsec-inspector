from __future__ import annotations

import copy
import json
import os
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

import httpx

from ..config import Settings
from ..models import Target
from ..security import validate_outbound_url


class LLMProtocolError(RuntimeError):
    """Raised when an endpoint response cannot be safely normalised."""


@dataclass
class LLMResult:
    text: str
    raw: dict[str, Any]
    tool_calls: list[dict[str, Any]]
    events: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    completed: bool | None = None
    request_payload: dict[str, Any] = field(default_factory=dict)
    request_url: str = ""


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
            raise LLMProtocolError(f"Chatbot response does not contain configured path {path!r}")
    return current


def _tool_key(value: dict[str, Any]) -> str:
    if value.get("id"):
        return f"id:{value['id']}"
    if value.get("index") is not None:
        return f"index:{value['index']}"
    function = value.get("function", {}) if isinstance(value.get("function"), dict) else {}
    name = value.get("name") or value.get("tool") or function.get("name")
    detail = value.get("detail") or value.get("arguments") or function.get("arguments")
    return json.dumps([name, value.get("target_id"), detail], sort_keys=True, ensure_ascii=False, default=str)


def _deduplicate_tools(values: list[Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    for value in values:
        if not isinstance(value, dict):
            continue
        key = _tool_key(value)
        if key not in seen:
            seen[key] = len(result)
            result.append(value)
        else:
            result[seen[key]] = {**result[seen[key]], **value}
    return result


def _known_text(raw: dict[str, Any]) -> tuple[str, str] | None:
    candidates = (
        ("response", raw.get("response")),
        ("text", raw.get("text")),
        ("answer", raw.get("answer")),
        ("message.content", raw.get("message", {}).get("content") if isinstance(raw.get("message"), dict) else None),
        ("answer.text", raw.get("answer", {}).get("text") if isinstance(raw.get("answer"), dict) else None),
        ("data.response", raw.get("data", {}).get("response") if isinstance(raw.get("data"), dict) else None),
    )
    for path, value in candidates:
        if isinstance(value, str):
            return value, path
    choices = raw.get("choices")
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        message = choices[0].get("message", {})
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            return message["content"], "choices.0.message.content"
    return None


def normalise_json(raw: Any, target_type: str, config: dict[str, Any]) -> LLMResult:
    if not isinstance(raw, dict):
        raise LLMProtocolError("LLM endpoint returned a non-object JSON response")
    if target_type in {"chatbot", "agent_lab"} and config.get("response_path"):
        path = str(config["response_path"])
        content = _get_json_path(raw, path, label="response_path")
        tool_path = str(config.get("tool_calls_path", ""))
        configured_tools = _get_json_path(raw, tool_path, label="tool_calls_path") if tool_path else []
        if not isinstance(content, str):
            raise LLMProtocolError("Configured chatbot response path does not contain text")
        if not isinstance(configured_tools, list):
            raise LLMProtocolError("Configured chatbot tool-calls path does not contain a list")
        return LLMResult(content, raw, _deduplicate_tools(configured_tools), metadata={"protocol": "json", "response_path": path})
    found = _known_text(raw)
    if not found:
        raise LLMProtocolError("No supported response text field was found in the JSON object")
    text, path = found
    message = raw.get("message", {}) if isinstance(raw.get("message"), dict) else {}
    choices = raw.get("choices", [])
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        message = choices[0].get("message", message)
    tools: list[Any] = []
    if isinstance(message, dict):
        tools.extend(message.get("tool_calls") or [])
    tools.extend(raw.get("tools") or [])
    return LLMResult(text, raw, _deduplicate_tools(tools), metadata={"protocol": "json", "response_path": path, "model": raw.get("model")}, completed=raw.get("completed") if isinstance(raw.get("completed"), bool) else None)


async def _bounded_lines(response: httpx.Response, maximum: int) -> AsyncIterator[str]:
    total = 0
    async for line in response.aiter_lines():
        total += len(line.encode("utf-8")) + 1
        if total > maximum:
            raise LLMProtocolError("LLM streaming response exceeded the configured size limit")
        if line.strip():
            yield line


async def normalise_ndjson(response: httpx.Response, maximum: int) -> LLMResult:
    events: list[dict[str, Any]] = []
    tokens: list[str] = []
    tools: list[Any] = []
    done: dict[str, Any] | None = None
    line_number = 0
    async for line in _bounded_lines(response, maximum):
        line_number += 1
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LLMProtocolError(f"Invalid NDJSON at line {line_number}: {exc.msg}") from exc
        if not isinstance(event, dict):
            raise LLMProtocolError(f"NDJSON line {line_number} is not a JSON object")
        events.append(event)
        event_type = event.get("type")
        if event_type == "token" and isinstance(event.get("text"), str):
            tokens.append(event["text"])
        elif event_type == "tool":
            tools.append(event)
        elif event_type == "done":
            done = event
            tools.extend(event.get("tools") or [])
        elif event_type == "error":
            raise LLMProtocolError(str(event.get("message") or "Streaming endpoint returned an error event"))
    if not events:
        raise LLMProtocolError("NDJSON stream ended without an event")
    token_text = "".join(tokens)
    final_text = done.get("response") if done and isinstance(done.get("response"), str) else token_text
    comparison = "unavailable"
    if done and isinstance(done.get("response"), str) and tokens:
        comparison = "match" if done["response"] == token_text else "mismatch"
    metadata = {"protocol": "ndjson", "model": done.get("model") if done else None, "continuations": done.get("continuations") if done else None, "token_response_comparison": comparison, "event_count": len(events)}
    completed = done.get("completed") if done and isinstance(done.get("completed"), bool) else None
    return LLMResult(str(final_text), done or events[-1], _deduplicate_tools(tools), events, metadata, completed)


async def normalise_sse(response: httpx.Response, maximum: int) -> LLMResult:
    events: list[dict[str, Any]] = []
    tokens: list[str] = []
    tools: list[Any] = []
    streamed_tools: dict[int, dict[str, Any]] = {}
    async for line in _bounded_lines(response, maximum):
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            break
        try:
            event = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise LLMProtocolError(f"Invalid SSE JSON event: {exc.msg}") from exc
        if not isinstance(event, dict):
            continue
        events.append(event)
        choices = event.get("choices", [])
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            delta = choices[0].get("delta", {})
            if isinstance(delta, dict):
                if isinstance(delta.get("content"), str):
                    tokens.append(delta["content"])
                for item in delta.get("tool_calls") or []:
                    if not isinstance(item, dict):
                        continue
                    index = int(item.get("index", len(streamed_tools)))
                    current = streamed_tools.setdefault(index, {"index": index})
                    if item.get("id"):
                        current["id"] = item["id"]
                    if item.get("type"):
                        current["type"] = item["type"]
                    function = item.get("function")
                    if isinstance(function, dict):
                        target_function = current.setdefault("function", {})
                        if function.get("name"):
                            target_function["name"] = function["name"]
                        if isinstance(function.get("arguments"), str):
                            target_function["arguments"] = str(target_function.get("arguments", "")) + function["arguments"]
        if isinstance(event.get("token"), dict) and isinstance(event["token"].get("text"), str):
            tokens.append(event["token"]["text"])
        if isinstance(event.get("text"), str):
            tokens.append(event["text"])
        tools.extend(event.get("tools") or [])
    if not events and not tokens:
        raise LLMProtocolError("SSE stream ended without a data event")
    tools.extend(streamed_tools.values())
    return LLMResult("".join(tokens), events[-1] if events else {}, _deduplicate_tools(tools), events, {"protocol": "sse", "event_count": len(events)}, True)


def _request_parts(target: Target, messages: list[dict[str, str]], max_tokens: int) -> tuple[str, dict[str, Any]]:
    config = target.configuration
    endpoint = target.endpoint or ""
    model = str(config.get("model", ""))
    if target.target_type == "ollama":
        return endpoint.rstrip("/") + "/api/chat", {"model": model, "messages": messages, "stream": bool(config.get("stream", False)), "options": {"num_predict": max_tokens}}
    if target.target_type in {"chatbot", "agent_lab"}:
        payload = copy.deepcopy(config.get("static_payload", {}))
        if not isinstance(payload, dict):
            raise ValueError("chatbot static_payload must be a JSON object")
        _set_json_path(payload, str(config.get("message_path", "message")), messages[-1]["content"], label="message_path")
        history_path = str(config.get("history_path", ""))
        if history_path:
            _set_json_path(payload, history_path, messages, label="history_path")
        max_tokens_path = str(config.get("max_tokens_path", ""))
        if max_tokens_path:
            _set_json_path(payload, max_tokens_path, max_tokens, label="max_tokens_path")
        return endpoint.rstrip("/"), payload
    url = endpoint.rstrip("/")
    if not url.endswith("/chat/completions"):
        url += "/v1/chat/completions"
    return url, {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0, "stream": bool(config.get("stream", False))}


def _headers(config: dict[str, Any]) -> dict[str, str]:
    headers = {"Content-Type": "application/json", "Accept": "application/json, application/x-ndjson, text/event-stream"}
    configured = config.get("headers", {})
    if configured:
        if not isinstance(configured, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in configured.items()):
            raise ValueError("Configured chatbot headers must be a string-to-string object")
        blocked = {"authorization", "proxy-authorization", "cookie", "host", "content-length", "transfer-encoding", "connection"}
        if any(not re.fullmatch(r"[A-Za-z0-9-]{1,100}", key) or key.casefold() in blocked or "\r" in value or "\n" in value or len(value) > 4096 for key, value in configured.items()):
            raise ValueError("Configured chatbot headers contain a forbidden name or invalid value")
        headers.update(configured)
    key_env = str(config.get("api_key_env", ""))
    if key_env:
        token = os.getenv(key_env)
        if not token:
            raise RuntimeError(f"Configured credential environment variable {key_env!r} is unavailable")
        key_header = str(config.get("api_key_header", "Authorization"))
        if not re.fullmatch(r"[A-Za-z0-9-]{1,100}", key_header):
            raise ValueError("Invalid API key header name")
        prefix = str(config.get("api_key_prefix", "Bearer"))
        if "\r" in prefix or "\n" in prefix or len(prefix) > 100:
            raise ValueError("Invalid API key prefix")
        headers[key_header] = f"{prefix} {token}".strip()
    return headers


async def send_chat(target: Target, messages: list[dict[str, str]], max_tokens: int, settings: Settings) -> LLMResult:
    config = target.configuration
    url, payload = _request_parts(target, messages, max_tokens)
    url = validate_outbound_url(url, remote_authorized=target.remote_authorized, settings=settings)
    response_format = str(config.get("response_format", "json")).casefold()
    if response_format not in {"auto", "json", "ndjson", "sse", "openai", "ollama"}:
        raise ValueError("response_format must be auto, json, ndjson, sse, openai, or ollama")
    timeout = httpx.Timeout(settings.request_timeout_seconds)
    # POST is never retried implicitly: a target may execute tools before the connection fails.
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        if response_format in {"json", "openai", "ollama"} and not bool(config.get("stream", False)):
            response = await client.post(url, headers=_headers(config), json=payload)
            response.raise_for_status()
            if len(response.content) > settings.max_response_bytes:
                raise LLMProtocolError("LLM response exceeded the configured size limit")
            try:
                raw = response.json()
            except json.JSONDecodeError as exc:
                raise LLMProtocolError(f"Invalid JSON response: {exc.msg}") from exc
            result = normalise_json(raw, target.target_type, config)
            result.metadata.update({"content_type": response.headers.get("content-type", "").casefold(), "endpoint_protocol": "json"})
            result.request_payload = copy.deepcopy(payload)
            result.request_url = url
            return result
        async with client.stream("POST", url, headers=_headers(config), json=payload) as response:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").casefold()
            protocol = response_format
            if protocol == "auto":
                protocol = "ndjson" if "ndjson" in content_type else "sse" if "event-stream" in content_type else "json"
            if protocol == "ndjson" or protocol == "ollama" and bool(config.get("stream", False)):
                result = await normalise_ndjson(response, settings.max_response_bytes)
            elif protocol == "sse" or protocol == "openai" and bool(config.get("stream", False)):
                result = await normalise_sse(response, settings.max_response_bytes)
            else:
                content = await response.aread()
                if len(content) > settings.max_response_bytes:
                    raise LLMProtocolError("LLM response exceeded the configured size limit")
                try:
                    raw = json.loads(content)
                except json.JSONDecodeError as exc:
                    raise LLMProtocolError(f"Invalid JSON response: {exc.msg}") from exc
                result = normalise_json(raw, target.target_type, config)
            result.metadata.update({"content_type": content_type, "endpoint_protocol": protocol})
            result.request_payload = copy.deepcopy(payload)
            result.request_url = url
            return result
