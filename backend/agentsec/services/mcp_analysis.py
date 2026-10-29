from __future__ import annotations

import re
from typing import Any

SENSITIVE_NAMES = re.compile(
    r"(delete|remove|exec|shell|admin|write|upload|credential|secret|token)", re.I
)
INSTRUCTION_TEXT = re.compile(
    r"(ignore (all|previous)|system prompt|do not tell|override instruction|act as)", re.I
)
PATH_NAMES = re.compile(r"(path|file|directory|folder|filename)", re.I)


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
        if SENSITIVE_NAMES.search(name + " " + description):
            observations.append(
                _item(
                    name,
                    "Sensitive capability exposed",
                    "The advertised capability may alter data, execute commands, or access sensitive material.",
                    description or name,
                    "high",
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
