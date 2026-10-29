from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
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
    Severity,
    Target,
    TestExecution,
)
from .events import event_hub
from .llm_client import send_chat
from .mcp_analysis import analyse_discovery
from .mcp_client import HTTPMCPClient, StdioMCPClient
from .scenarios import SCENARIOS, evaluate, scenario_messages

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
            elif target.target_type == "mcp_stdio":
                async with StdioMCPClient(
                    str(config.get("command", "")), list(config.get("args", [])), settings
                ) as stdio_client:
                    discovered = await stdio_client.discover()
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
            evidence_text = _bounded_json(payload)
            evidence = Evidence(
                project_id=audit.project_id,
                evidence_type="mcp_discovery",
                title="MCP passive discovery",
                content=evidence_text,
                sha256=hashlib.sha256(evidence_text.encode()).hexdigest(),
            )
            db.add(evidence)
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
            audit.summary = {
                "tools": len(discovered.tools),
                "resources": len(discovered.resources),
                "prompts": len(discovered.prompts),
                "observations": len(issues),
                "discovery": payload,
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
            scenario = next(
                (item for item in SCENARIOS if item["id"] == request["scenario_id"]), None
            )
            if not scenario:
                raise ValueError("Unknown scenario")
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
            result = await send_chat(target, messages, int(request["max_tokens"]), settings)
            status, analysis = evaluate(result.text, result.tool_calls, request["fictional_marker"])
            execution.status = status
            execution.response_data = {"text": result.text, "tool_calls": result.tool_calls}
            execution.analysis = analysis
            execution.finished_at = utcnow()
            evidence_text = _bounded_json(
                {
                    "request": messages,
                    "response": result.text,
                    "tool_calls": result.tool_calls,
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
                        "status": status,
                        "tool_calls": len(result.tool_calls),
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
                        observed_result=result.text[:20_000],
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


def _bounded_json(value: Any) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, indent=2, default=str)[:200_000]
