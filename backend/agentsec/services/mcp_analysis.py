from __future__ import annotations

import json
import re
from typing import Any

SENSITIVE_TOOL_NAMES = re.compile(
    r"(?:^|[_\-\s])(delete|remove|exec|execute|shell|admin|write|upload|"
    r"credential|secret|token|password|transfer|send|create|update|book|reply)"
    r"(?:$|[_\-\s])", re.I
)
SENSITIVE_DESCRIPTION_ACTIONS = re.compile(
    r"\b(delete|remove|execute|run commands?|transfer money|"
    r"write (?:a |the )?(?:file|record)|administrative delete)\b", re.I
)
INSTRUCTION_TEXT = re.compile(
    r"(ignore (all|previous)|system prompt|do not tell|override instruction|act as)", re.I
)
PATH_NAMES = re.compile(r"(path|file|directory|folder|filename)", re.I)


def is_sensitive_tool(tool: dict[str, Any] | str) -> bool:
    """Identify potentially mutating tools without keyword-matching incidental prose.

    A description mentioning a session token or progressToken is not evidence of
    a dangerous capability. MCP annotations are advisory, not trusted security
    guarantees: explicit risky actions remain sensitive even if readOnlyHint
    claims otherwise.
    """
    if isinstance(tool, str):
        return bool(SENSITIVE_TOOL_NAMES.search(tool))
    name = str(tool.get("name", ""))
    description = str(tool.get("description", ""))
    annotations = tool.get("annotations") or {}
    return (
        bool(SENSITIVE_TOOL_NAMES.search(name))
        or bool(SENSITIVE_DESCRIPTION_ACTIONS.search(description))
        or (isinstance(annotations, dict) and annotations.get("destructiveHint") is True)
        or (isinstance(annotations, dict) and annotations.get("readOnlyHint") is False)
    )


def analyse_tool_result(tool_name: str, result: dict[str, Any]) -> list[dict[str, Any]]:
    text = json.dumps(result, ensure_ascii=False, default=str)
    if not INSTRUCTION_TEXT.search(text):
        return []
    return [
        _item(
            tool_name,
            "Instruction-like content returned by MCP tool",
            "The observed tool result contains instruction-like language that could influence an agent.",
            text,
            "medium",
            "medium",
            "Risk potential",
            "Treat tool output as untrusted data and preserve instruction boundaries before LLM use.",
        )
    ]


def analyse_discovery(discovery: dict[str, Any]) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    names: dict[str, int] = {}
    for tool in discovery.get("tools", []):
        name = str(tool.get("name", "unnamed"))
        description = str(tool.get("description", ""))
        schema = tool.get("inputSchema") or {}
        names[name.casefold()] = names.get(name.casefold(), 0) + 1
        if INSTRUCTION_TEXT.search(description):
            observations.append(
                _item(
                    name,
                    "Suspicious instruction-like tool description",
                    "Tool description contains language that may influence an agent instruction hierarchy.",
                    description,
                    "medium",
                    "medium",
                    "Risk potential",
                    "Review and rewrite the description as neutral capability documentation.",
                )
            )
        if is_sensitive_tool(tool):
            observations.append(
                _item(
                    name,
                    "Sensitive capability exposed",
                    "The advertised capability may alter data, execute commands, or access sensitive material.",
                    description or name,
                    "info",
                    "medium",
                    "Observation",
                    "Apply least privilege, confirmation gates and server-side authorisation.",
                )
            )
        properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
        for parameter, definition in properties.items():
            if (
                PATH_NAMES.search(parameter)
                and isinstance(definition, dict)
                and not any(key in definition for key in ("pattern", "enum", "const"))
            ):
                observations.append(
                    _item(
                        name,
                        f"Unconstrained path parameter: {parameter}",
                        "A filesystem-like input has no advertised pattern or allowlist constraint.",
                        str(definition),
                        "medium",
                        "medium",
                        "Risk potential",
                        "Constrain paths server-side to an authorised root; reject traversal and absolute paths.",
                    )
                )
        if (
            isinstance(schema, dict)
            and schema.get("type") == "object"
            and properties
            and "additionalProperties" not in schema
        ):
            observations.append(
                _item(
                    name,
                    "Input schema accepts unspecified properties",
                    "The schema does not explicitly reject additional properties.",
                    str(schema),
                    "low",
                    "high",
                    "Observation",
                    "Set additionalProperties to false when unknown inputs are not required.",
                )
            )
    for name, count in names.items():
        if count > 1:
            observations.append(
                _item(
                    name,
                    "Duplicate tool name",
                    "Multiple advertised tools share a case-insensitive name, creating tool-selection ambiguity.",
                    f"count={count}",
                    "medium",
                    "high",
                    "Risk potential",
                    "Use unique, unambiguous tool names.",
                )
            )
    return observations


def _item(
    component: str,
    title: str,
    description: str,
    evidence: str,
    severity: str,
    confidence: str,
    classification: str,
    recommendation: str,
) -> dict[str, Any]:
    return {
        "component": component,
        "title": title,
        "description": description,
        "evidence": evidence[:20_000],
        "severity": severity,
        "confidence": confidence,
        "classification": classification,
        "recommendation": recommendation,
    }


def analyse_vulnerabilities(discovery: dict[str, Any]) -> list[dict[str, Any]]:
    """Passive security assessment of advertised MCP interfaces.

    Identifies suspicious attack surfaces, not confirmed exploitation. Never
    invokes a tool, fetches resources, or sends payloads to third parties.
    """
    findings: list[dict[str, Any]] = []
    for tool in discovery.get("tools", []):
        if not isinstance(tool, dict):
            continue
        name = str(tool.get("name", "unnamed"))
        description = str(tool.get("description", ""))
        schema = tool.get("inputSchema") or {}
        annotations = tool.get("annotations") or {}
        if not isinstance(schema, dict):
            findings.append(_item(
                name, "Invalid MCP input schema",
                "Tool inputSchema is not an object; clients cannot reliably validate arguments.",
                repr(schema), "medium", "high", "Risk potential",
                "Publish a valid JSON Schema object and validate arguments server-side.",
            ))
            continue
        if is_sensitive_tool(tool) and isinstance(annotations, dict) and annotations.get("readOnlyHint") is True:
            findings.append(_item(
                name, "Potentially dangerous tool marked read-only",
                "Tool capability or description suggests mutation despite readOnlyHint=true.",
                json.dumps({"description": description, "annotations": annotations}, ensure_ascii=False),
                "medium", "medium", "Risk potential",
                "Correct annotations and enforce authorization, approval and server-side permissions.",
            ))
        properties = schema.get("properties") or {}
        if not isinstance(properties, dict):
            findings.append(_item(
                name, "Malformed MCP input properties",
                "Input properties is not a JSON Schema object.",
                repr(properties), "medium", "high", "Risk potential",
                "Publish well-formed input properties and validate all inputs.",
            ))
        elif schema.get("additionalProperties") is True and is_sensitive_tool(tool):
            findings.append(_item(
                name, "Sensitive tool explicitly accepts arbitrary arguments",
                "Tool declares additionalProperties=true on a potentially mutating capability.",
                json.dumps(schema, ensure_ascii=False)[:5000], "medium", "medium", "Risk potential",
                "Use an allowlisted schema and enforce strict server-side input validation.",
            ))
    for resource in discovery.get("resources", []):
        if not isinstance(resource, dict):
            continue
        uri = str(resource.get("uri", ""))
        if not uri or any(uri.lower().startswith(prefix) for prefix in (
            "file:///etc/", "file:///root/", "file:///home/", "file:///c:/windows/"
        )):
            findings.append(_item(
                uri[:200] or "unnamed resource", "Exposed or invalid resource URI",
                "A listed resource has no URI or advertises a sensitive local filesystem location.",
                json.dumps(resource, ensure_ascii=False)[:5000],
                "medium", "medium", "Risk potential",
                "Publish least-privilege resource URIs and enforce resource access controls.",
            ))
    for prompt in discovery.get("prompts", []):
        if not isinstance(prompt, dict):
            continue
        description = str(prompt.get("description", ""))
        if INSTRUCTION_TEXT.search(description):
            findings.append(_item(
                str(prompt.get("name", "unnamed")), "Instruction-like MCP prompt metadata",
                "Advertised prompt metadata includes instruction-like content that may influence agents.",
                description, "medium", "medium", "Risk potential",
                "Separate untrusted metadata from trusted instructions and audit prompt sources.",
            ))
    return findings
