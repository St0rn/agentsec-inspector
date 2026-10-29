from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import AgentEvent, AuditRun, Project, Scenario, Target
from ..schemas import AuditRead, MCPAuditRequest, PromptTestRequest, ScenarioPackImport
from ..services.audits import run_mcp_audit, run_prompt_test
from ..services.events import event_hub
from ..services.mcp_analysis import is_sensitive_tool

router = APIRouter(tags=["audits"])


@router.get("/scenarios")
async def list_scenarios(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    rows = db.scalars(
        select(Scenario).where(Scenario.active.is_(True)).order_by(Scenario.category, Scenario.name)
    )
    return [
        {
            "id": row.id,
            "version": row.version,
            "name": row.name,
            "description": row.description,
            "category": row.category,
            "prerequisites": row.prerequisites,
            "configuration": row.configuration,
            "procedure": row.procedure,
            "success_criteria": row.success_criteria,
            "failure_criteria": row.failure_criteria,
            "references": row.references,
        }
        for row in rows
    ]


@router.post("/scenarios/import", status_code=201)
async def import_scenario_pack(
    body: ScenarioPackImport, db: Session = Depends(get_db)
) -> dict[str, object]:
    imported = 0
    updated = 0
    for definition in body.scenarios:
        item = db.get(Scenario, (definition.id, definition.version))
        if item and not body.replace_existing:
            raise HTTPException(
                409,
                f"Scenario {definition.id}@{definition.version} already exists; set replace_existing explicitly",
            )
        values = definition.model_dump()
        values["configuration"] = {
            **values["configuration"],
            "scenario_pack": {
                "id": body.pack_id,
                "version": body.pack_version,
                "name": body.name,
            },
        }
        if item:
            for key, value in values.items():
                setattr(item, key, value)
            item.active = True
            updated += 1
        else:
            db.add(Scenario(**values))
            imported += 1
    db.commit()
    return {
        "pack_id": body.pack_id,
        "pack_version": body.pack_version,
        "imported": imported,
        "updated": updated,
        "code_execution": False,
    }


@router.get("/audits", response_model=list[AuditRead])
async def list_audits(
    project_id: str | None = None, db: Session = Depends(get_db)
) -> list[AuditRun]:
    statement = select(AuditRun).order_by(AuditRun.created_at.desc())
    if project_id:
        statement = statement.where(AuditRun.project_id == project_id)
    return list(db.scalars(statement))


@router.get("/audits/{audit_id}", response_model=AuditRead)
async def get_audit(audit_id: str, db: Session = Depends(get_db)) -> AuditRun:
    audit = db.get(AuditRun, audit_id)
    if not audit:
        raise HTTPException(404, "Audit not found")
    return audit


@router.post("/audits/mcp", response_model=AuditRead, status_code=202)
async def start_mcp_audit(body: MCPAuditRequest, db: Session = Depends(get_db)) -> AuditRun:
    target = _validate_target(db, body.project_id, body.target_id)
    if target.target_type not in {"mcp_http", "mcp_stdio"}:
        raise HTTPException(422, "Target is not MCP")
    if not body.passive and not body.confirm_active_operations:
        raise HTTPException(409, "Active operations require explicit confirmation")
    for call in body.active_tool_calls:
        if is_sensitive_tool(call.tool_name) and not call.confirm_sensitive_operation:
            raise HTTPException(
                409,
                f"Sensitive MCP tool {call.tool_name!r} requires individual confirmation",
            )
    audit = AuditRun(
        project_id=body.project_id,
        target_id=body.target_id,
        audit_type="mcp_security",
        passive=body.passive,
        configuration={
            "confirmed_active": body.confirm_active_operations,
            "active_tool_calls": [item.model_dump() for item in body.active_tool_calls],
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    asyncio.create_task(run_mcp_audit(audit.id))
    return audit


@router.post("/audits/prompt", response_model=AuditRead, status_code=202)
async def start_prompt_test(body: PromptTestRequest, db: Session = Depends(get_db)) -> AuditRun:
    target = _validate_target(db, body.project_id, body.target_id)
    if target.target_type not in {"openai", "ollama", "custom_http", "chatbot", "agent_lab"}:
        raise HTTPException(422, "Target is not an LLM chat endpoint")
    if not body.confirm_active_test:
        raise HTTPException(409, "Sending an active test requires explicit confirmation")
    scenario = db.get(Scenario, (body.scenario_id, body.scenario_version))
    if not scenario:
        raise HTTPException(404, "Scenario not found")
    audit = AuditRun(
        project_id=body.project_id,
        target_id=body.target_id,
        audit_type="jailbreak" if scenario.category == "jailbreak" else "prompt_injection",
        passive=False,
        configuration={
            "scenario_id": body.scenario_id,
            "scenario_version": body.scenario_version,
            "security_objective": body.security_objective,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    asyncio.create_task(run_prompt_test(audit.id, body.model_dump()))
    return audit


@router.get("/agent-events")
async def list_agent_events(
    project_id: str, audit_id: str | None = None, db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    statement = (
        select(AgentEvent)
        .where(AgentEvent.project_id == project_id)
        .order_by(AgentEvent.occurred_at)
    )
    if audit_id:
        statement = statement.where(AgentEvent.audit_run_id == audit_id)
    rows = db.scalars(statement)
    return [
        {
            "id": row.id,
            "audit_run_id": row.audit_run_id,
            "event_type": row.event_type,
            "actor": row.actor,
            "target": row.target,
            "payload": row.payload,
            "duration_ms": row.duration_ms,
            "occurred_at": row.occurred_at,
        }
        for row in rows
    ]


@router.websocket("/audits/{audit_id}/events")
async def audit_events(websocket: WebSocket, audit_id: str, token: str = "") -> None:
    if token != get_settings().api_token:
        await websocket.close(code=4401)
        return
    await event_hub.connect(audit_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await event_hub.disconnect(audit_id, websocket)


def _validate_target(db: Session, project_id: str, target_id: str) -> Target:
    if not db.get(Project, project_id):
        raise HTTPException(404, "Project not found")
    target = db.get(Target, target_id)
    if not target or target.project_id != project_id:
        raise HTTPException(404, "Target not found in project")
    return target
