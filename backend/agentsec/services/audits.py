from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

import structlog
from sqlalchemy import select

from ..config import get_settings
from ..database import SessionLocal
from ..models import (
    AgentEvent,
    AuditRun,
    AuditStatus,
    Evidence,
    Finding,
    Scenario,
    Severity,
    Target,
    TestExecution,
)
from .events import event_hub
from .llm_client import send_chat
from .mcp_analysis import analyse_discovery, analyse_tool_result, is_sensitive_tool
from .mcp_client import HTTPMCPClient, StdioMCPClient
from .scenarios import evaluate, scenario_messages

log = structlog.get_logger()


def utcnow() -> datetime:
    return datetime.now(UTC)


async def run_mcp_audit(audit_id: str) -> None:
    settings = get_settings()
    with SessionLocal() as db:
        audit = db.get(AuditRun, audit_id)
        if not audit:
            return
        audit.status = AuditStatus.running
        audit.started_at = utcnow()
        target = db.get(Target, audit.target_id)
        db.commit()
        if not target:
            await _fail(db, audit, "Target not found")
            return
        await event_hub.publish(audit_id, {"stage": "connecting", "progress": 10})
        try:
            config = target.configuration
            requested_calls = list(audit.configuration.get("active_tool_calls", []))
            active_results: list[dict[str, Any]] = []
            if target.target_type == "mcp_http":
                headers = dict(config.get("headers", {}))
                auth_env = str(config.get("auth_env", ""))
                if auth_env:
                    token = os.getenv(auth_env)
                    if not token:
                        raise RuntimeError(
                            f"Configured credential environment variable {auth_env!r} is unavailable"
                        )
                    headers["Authorization"] = f"Bearer {token}"
                http_client = HTTPMCPClient(
                    target.endpoint or "", headers, settings, target.remote_authorized
                )
                discovered = await http_client.discover()
                if not audit.passive:
                    active_results = await execute_active_tool_calls(
                        http_client, discovered.tools, requested_calls
                    )
            elif target.target_type == "mcp_stdio":
                async with StdioMCPClient(
                    str(config.get("command", "")), list(config.get("args", [])), settings
                ) as stdio_client:
                    discovered = await stdio_client.discover()
                    if not audit.passive:
                        active_results = await execute_active_tool_calls(
                            stdio_client, discovered.tools, requested_calls
                        )
            else:
                raise ValueError("Selected target is not an MCP target")
            payload = {
                "server_info": discovered.server_info,
                "capabilities": discovered.capabilities,
                "tools": discovered.tools,
                "resources": discovered.resources,
                "prompts": discovered.prompts,
            }
            await event_hub.publish(
                audit_id, {"stage": "analysing", "progress": 60, "tools": len(discovered.tools)}
            )
            issues = analyse_discovery(payload)
            for execution in active_results:
                if execution["status"] == "SUCCESS":
                    issues.extend(analyse_tool_result(execution["tool_name"], execution["result"]))
            evidence_text = _bounded_json(payload)
            evidence = Evidence(
                project_id=audit.project_id,
                evidence_type="mcp_discovery",
                title="MCP capability discovery",
                content=evidence_text,
                sha256=hashlib.sha256(evidence_text.encode()).hexdigest(),
            )
            db.add(evidence)
            if active_results:
                active_evidence_text = _bounded_json({"tool_calls": active_results})
                db.add(
                    Evidence(
                        project_id=audit.project_id,
                        evidence_type="mcp_active_tool_calls",
                        title="Explicitly authorised MCP active calls",
                        content=active_evidence_text,
                        sha256=hashlib.sha256(active_evidence_text.encode()).hexdigest(),
                    )
                )
            for issue in issues:
                finding = Finding(
                    project_id=audit.project_id,
                    audit_run_id=audit.id,
                    title=issue["title"],
                    description=issue["description"],
                    component=issue["component"],
                    classification=issue["classification"],
                    severity=Severity(issue["severity"]),
                    confidence=issue["confidence"],
                    observed_result=issue["evidence"],
                    expected_result="Capability documentation and schema should support safe, unambiguous use.",
                    recommendation=issue["recommendation"],
                )
                db.add(finding)
            db.add(
                AgentEvent(
                    project_id=audit.project_id,
                    audit_run_id=audit.id,
                    event_type="mcp_discovery",
                    actor="AgentSec",
                    target=target.name,
                    payload={
                        "tool_count": len(discovered.tools),
                        "resource_count": len(discovered.resources),
                        "prompt_count": len(discovered.prompts),
                    },
                )
            )
            for execution in active_results:
                db.add(
                    AgentEvent(
                        project_id=audit.project_id,
                        audit_run_id=audit.id,
                        event_type="mcp_tool_call",
                        actor="AgentSec",
                        target=execution["tool_name"],
                        payload={
                            "arguments": execution["arguments"],
                            "status": execution["status"],
                            "sensitive": execution["sensitive"],
                        },
                        duration_ms=execution["duration_ms"],
                    )
                )
            audit.summary = {
                "tools": len(discovered.tools),
                "resources": len(discovered.resources),
                "prompts": len(discovered.prompts),
                "observations": len(issues),
                "discovery": payload,
                "mode": "passive" if audit.passive else "active",
                "active_tool_calls": active_results,
            }
            audit.status = AuditStatus.completed
            audit.finished_at = utcnow()
            db.commit()
            await event_hub.publish(
                audit_id, {"stage": "completed", "progress": 100, "observations": len(issues)}
            )
        except Exception as exc:
            log.warning("mcp_audit_failed", audit_id=audit_id, error=str(exc))
            await _fail(db, audit, str(exc))


async def run_prompt_test(audit_id: str, request: dict[str, Any]) -> None:
    settings = get_settings()
    with SessionLocal() as db:
        audit = db.get(AuditRun, audit_id)
        if not audit:
            return
        audit.status = AuditStatus.running
        audit.started_at = utcnow()
        target = db.get(Target, audit.target_id)
        db.commit()
        await event_hub.publish(audit_id, {"stage": "requesting", "progress": 20})
        try:
            if not target:
                raise ValueError("Target not found")
            scenario_record = db.get(
                Scenario, (request["scenario_id"], request.get("scenario_version", "1.0.0"))
            )
            if not scenario_record:
                raise ValueError("Unknown scenario")
            chat_steps = [
                item
                for item in scenario_record.procedure
                if item.get("type") == "chat" and isinstance(item.get("template"), str)
            ]
            if not chat_steps:
                raise ValueError("Scenario has no supported declarative chat step")
            scenario = {
                "id": scenario_record.id,
                "version": scenario_record.version,
                "name": scenario_record.name,
                "category": scenario_record.category,
                "template": chat_steps[0]["template"],
            }
            messages = scenario_messages(
                scenario, request["fictional_marker"], request["system_instruction"]
            )
            execution = TestExecution(
                audit_run_id=audit.id,
                scenario_id=scenario["id"],
                scenario_version=scenario["version"],
                status="RUNNING",
                request_data={
                    "messages": messages,
                    "security_objective": request["security_objective"],
                },
            )
            db.add(execution)
            db.commit()
            turns: list[dict[str, Any]] = []
            all_tool_calls: list[dict[str, Any]] = []
            for index, step in enumerate(chat_steps):
                if index:
                    messages.append(
                        {
                            "role": "user",
                            "content": step["template"].format(marker=request["fictional_marker"]),
                        }
                    )
                result = await send_chat(target, messages, int(request["max_tokens"]), settings)
                turns.append(
                    {
                        "step": index + 1,
                        "response": result.text,
                        "tool_calls": result.tool_calls,
                    }
                )
                all_tool_calls.extend(result.tool_calls)
                if index < len(chat_steps) - 1:
                    messages.append({"role": "assistant", "content": result.text})
            combined_response = "\n\n".join(str(turn["response"]) for turn in turns)
            status, analysis = evaluate(
                combined_response, all_tool_calls, request["fictional_marker"]
            )
            execution.status = status
            execution.request_data = {
                "messages": messages,
                "security_objective": request["security_objective"],
            }
            execution.response_data = {
                "text": turns[-1]["response"],
                "tool_calls": all_tool_calls,
                "turns": turns,
            }
            execution.analysis = analysis
            execution.finished_at = utcnow()
            evidence_text = _bounded_json(
                {
                    "request": messages,
                    "response_turns": turns,
                    "tool_calls": all_tool_calls,
                    "analysis": analysis,
                }
            )
            evidence = Evidence(
                project_id=audit.project_id,
                evidence_type="prompt_test",
                title=f"Prompt test {scenario['name']}",
                content=evidence_text,
                sha256=hashlib.sha256(evidence_text.encode()).hexdigest(),
            )
            db.add(evidence)
            db.add(
                AgentEvent(
                    project_id=audit.project_id,
                    audit_run_id=audit.id,
                    event_type="llm_exchange",
                    actor="AgentSec",
                    target=target.name,
                    payload={
                        "scenario": scenario["id"],
                        "category": scenario["category"],
                        "status": status,
                        "turns": len(turns),
                        "tool_calls": len(all_tool_calls),
                    },
                )
            )
            if status == "FAIL":
                db.add(
                    Finding(
                        project_id=audit.project_id,
                        audit_run_id=audit.id,
                        title=f"Security objective violated: {scenario['name']}",
                        description="The real endpoint response disclosed the fictional marker or attempted a tool call under the controlled scenario.",
                        component=target.name,
                        classification="Confirmed vulnerability",
                        severity=Severity.high,
                        confidence="high",
                        impact="An untrusted instruction may influence protected output or agent actions.",
                        exploitation_conditions="A user or retrieved source can supply adversarial instructions.",
                        reproduction_steps=_bounded_json(messages),
                        observed_result=combined_response[:20_000],
                        expected_result="The endpoint should preserve instruction priority and avoid unauthorised tool attempts.",
                        recommendation="Separate untrusted content from instructions, enforce tool authorisation outside the model, and add output controls.",
                        frameworks=[
                            {
                                "framework": "OWASP Top 10 for LLM Applications",
                                "version": "2025",
                                "id": "LLM01",
                            }
                        ],
                    )
                )
            audit.summary = {
                "scenario": scenario["id"],
                "scenario_version": scenario["version"],
                "category": scenario["category"],
                "turns": len(turns),
                "test_status": status,
                "analysis": analysis,
            }
            audit.status = AuditStatus.completed
            audit.finished_at = utcnow()
            db.commit()
            await event_hub.publish(
                audit_id, {"stage": "completed", "progress": 100, "status": status}
            )
        except Exception as exc:
            current = db.scalar(
                select(TestExecution)
                .where(TestExecution.audit_run_id == audit.id)
                .order_by(TestExecution.started_at.desc())
            )
            if current:
                current.status = "ERROR"
                current.analysis = {"technical_error": str(exc), "attack_success": False}
                current.finished_at = utcnow()
            log.warning("prompt_test_failed", audit_id=audit_id, error=str(exc))
            await _fail(db, audit, str(exc))


async def _fail(db: Any, audit: AuditRun, message: str) -> None:
    audit.status = AuditStatus.failed
    audit.error = message[:10_000]
    audit.finished_at = utcnow()
    db.commit()
    await event_hub.publish(audit.id, {"stage": "failed", "progress": 100, "error": message})


async def execute_active_tool_calls(
    client: Any, advertised_tools: list[dict[str, Any]], requested_calls: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    tools = {str(item.get("name", "")): item for item in advertised_tools}
    executions: list[dict[str, Any]] = []
    for request in requested_calls:
        name = str(request.get("tool_name", ""))
        tool = tools.get(name)
        if not tool:
            raise ValueError(f"MCP tool {name!r} is not advertised by the selected target")
        arguments = request.get("arguments", {})
        if not isinstance(arguments, dict):
            raise ValueError(f"Arguments for MCP tool {name!r} must be an object")
        validate_mcp_arguments(tool.get("inputSchema") or {}, arguments)
        sensitive = is_sensitive_tool(tool)
        if sensitive and not request.get("confirm_sensitive_operation", False):
            raise PermissionError(
                f"Sensitive MCP tool {name!r} requires explicit individual confirmation"
            )
        started = perf_counter()
        try:
            result = await client.call_tool(name, arguments)
            status = "ERROR" if result.get("isError") is True else "SUCCESS"
            error = "MCP tool returned isError=true" if status == "ERROR" else None
        except Exception as exc:
            result = {}
            status = "ERROR"
            error = str(exc)[:10_000]
        executions.append(
            {
                "tool_name": name,
                "arguments": redact_secrets(arguments),
                "sensitive": sensitive,
                "status": status,
                "duration_ms": round((perf_counter() - started) * 1000),
                "result": redact_secrets(result),
                "error": error,
            }
        )
    return executions


def validate_mcp_arguments(schema: dict[str, Any], arguments: dict[str, Any]) -> None:
    if not isinstance(schema, dict) or not schema:
        return
    required = schema.get("required", [])
    missing = [name for name in required if name not in arguments]
    if missing:
        raise ValueError(f"Missing required MCP arguments: {', '.join(missing)}")
    properties = schema.get("properties", {})
    if schema.get("additionalProperties") is False:
        unknown = sorted(set(arguments) - set(properties))
        if unknown:
            raise ValueError(f"Unknown MCP arguments: {', '.join(unknown)}")
    type_checks: dict[str, Any] = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "object": dict,
        "array": list,
    }
    for name, value in arguments.items():
        definition = properties.get(name, {})
        if not isinstance(definition, dict):
            continue
        expected = definition.get("type")
        expected_type = type_checks.get(expected) if isinstance(expected, str) else None
        if expected_type and (
            not isinstance(value, expected_type)
            or expected == "integer"
            and isinstance(value, bool)
        ):
            raise ValueError(f"MCP argument {name!r} must be of type {expected}")
        if "enum" in definition and value not in definition["enum"]:
            raise ValueError(f"MCP argument {name!r} is outside its advertised enum")
        if "const" in definition and value != definition["const"]:
            raise ValueError(f"MCP argument {name!r} does not match its advertised constant")


def redact_secrets(value: Any) -> Any:
    secret_names = {"authorization", "password", "secret", "token", "api_key", "apikey"}
    if isinstance(value, dict):
        return {
            key: "***REDACTED***" if key.casefold() in secret_names else redact_secrets(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    return value


def _bounded_json(value: Any) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, indent=2, default=str)[:200_000]
