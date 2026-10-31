from __future__ import annotations

import asyncio
import io
import json

from fastapi import APIRouter, Depends, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import (
    AgentEvent,
    AppSetting,
    AuditRun,
    AuditStatus,
    Evidence,
    Finding,
    FindingOccurrence,
    RAGDocument,
    Project,
    Scenario,
    Target,
    TestExecution,
)
from ..schemas import (
    AuditRead,
    CustomPayloadRequest,
    GraphLayoutUpdate,
    MCPAuditRequest,
    PromptTestRequest,
    RAGActiveAuditRequest,
    ScenarioPackImport,
)
from ..services.audits import run_mcp_audit, run_prompt_test
from ..services.events import event_hub
from ..services.rag_active import run_rag_audit
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
            "expected_marker": row.expected_marker,
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
    project_id: str | None = None,
    audit_type: str | None = None,
    status: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
) -> list[AuditRun]:
    statement = select(AuditRun).order_by(AuditRun.created_at.desc())
    if project_id:
        statement = statement.where(AuditRun.project_id == project_id)
    if audit_type:
        statement = statement.where(AuditRun.audit_type == audit_type)
    if status:
        statement = statement.where(AuditRun.status == status)
    if search:
        pattern = f"%{search[:200]}%"
        statement = statement.outerjoin(Target, Target.id == AuditRun.target_id).where(
            or_(AuditRun.id.ilike(pattern), AuditRun.audit_type.ilike(pattern), Target.name.ilike(pattern))
        )
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


@router.post("/audits/rag", response_model=AuditRead, status_code=202)
async def start_rag_audit(
    body: RAGActiveAuditRequest, db: Session = Depends(get_db)
) -> AuditRun:
    target = _validate_target(db, body.project_id, body.target_id)
    if target.target_type not in {"rag", "chatbot", "agent_lab", "custom_http", "openai", "ollama"}:
        raise HTTPException(422, "Target is not a compatible RAG or chat endpoint")
    if not target.endpoint:
        raise HTTPException(422, "Active RAG testing requires a configured target endpoint")
    if not body.confirm_active_test:
        raise HTTPException(409, "RAG active testing requires explicit confirmation")
    if body.upload_document_id:
        document = db.get(RAGDocument, body.upload_document_id)
        if document is None or document.project_id != body.project_id or not document.is_lab_document:
            raise HTTPException(422, "Only imported controlled laboratory documents can be uploaded")
        if not body.confirm_document_upload or not target.configuration.get("ingest_endpoint"):
            raise HTTPException(409, "Document upload requires explicit approval and a configured ingestion endpoint")
    for case in body.cases:
        if case.kind != "baseline" and case.marker.casefold() in case.query.casefold():
            raise HTTPException(422, "Indirect injection markers must be supplied by retrieved material, not the user query")
    audit = AuditRun(
        project_id=body.project_id, target_id=body.target_id,
        audit_type="rag_security", passive=False,
        configuration={
            "cases": [item.model_dump() for item in body.cases],
            "upload_document_id": body.upload_document_id,
            "confirmed_active": True,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    asyncio.create_task(run_rag_audit(audit.id, body.model_dump()))
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
            "security_rules": [rule.model_dump() for rule in body.security_rules],
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    asyncio.create_task(run_prompt_test(audit.id, body.model_dump()))
    return audit


@router.post("/audits/custom", response_model=AuditRead, status_code=202)
async def start_custom_test(body: CustomPayloadRequest, db: Session = Depends(get_db)) -> AuditRun:
    target = _validate_target(db, body.project_id, body.target_id)
    if target.target_type in {"mcp_http", "mcp_stdio", "rag"}:
        raise HTTPException(422, "Custom chat payloads require an LLM or agent endpoint")
    if not body.confirm_active_test:
        raise HTTPException(409, "Sending a custom payload requires explicit confirmation")
    audit = AuditRun(
        project_id=body.project_id,
        target_id=body.target_id,
        audit_type="custom_payload",
        passive=False,
        configuration={
            "name": body.name,
            "category": body.category,
            "security_objective": body.security_objective,
            "security_rules": [rule.model_dump() for rule in body.security_rules],
            "payload_count": len(body.payloads),
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    request = body.model_dump()
    request.update(
        {
            "scenario_id": f"custom.{audit.id}",
            "scenario_version": "1.0.0",
            "custom_payloads": body.payloads,
        }
    )
    asyncio.create_task(run_prompt_test(audit.id, request))
    return audit


@router.delete("/audits/{audit_id}", status_code=204)
async def delete_audit(audit_id: str, confirm_delete: bool = False, db: Session = Depends(get_db)) -> Response:
    """Delete one historical execution and its audit-bound evidence, not shared findings."""
    if not confirm_delete:
        raise HTTPException(409, "Audit deletion requires explicit confirmation")
    audit = db.get(AuditRun, audit_id)
    if not audit:
        raise HTTPException(404, "Audit not found")
    if audit.status in {AuditStatus.queued, AuditStatus.running}:
        raise HTTPException(409, "Cannot delete an audit while it is running")
    # A finding may have been observed by multiple runs: keep the finding,
    # with its original audit association cleared by ON DELETE SET NULL.
    db.delete(audit)
    db.commit()
    return Response(status_code=204)


@router.delete("/audits", status_code=200)
async def delete_audit_history(
    confirm_delete: bool = False,
    project_id: str | None = None,
    audit_type: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, int]:
    if not confirm_delete:
        raise HTTPException(409, "Bulk audit deletion requires explicit confirmation")
    if not project_id:
        raise HTTPException(422, "A project_id is required for bulk deletion")
    if not db.get(Project, project_id):
        raise HTTPException(404, "Project not found")
    statement = select(AuditRun).where(AuditRun.project_id == project_id)
    if audit_type:
        statement = statement.where(AuditRun.audit_type == audit_type)
    audits = list(db.scalars(statement))
    if any(item.status in {AuditStatus.queued, AuditStatus.running} for item in audits):
        raise HTTPException(409, "Cannot clear history while matching audits are running")
    for audit in audits:
        db.delete(audit)
    db.commit()
    return {"deleted": len(audits)}


@router.get("/audits/{audit_id}/detail")
async def audit_detail(audit_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    audit = db.get(AuditRun, audit_id)
    if not audit:
        raise HTTPException(404, "Audit not found")
    target = db.get(Target, audit.target_id) if audit.target_id else None
    executions = list(db.scalars(select(TestExecution).where(TestExecution.audit_run_id == audit.id).order_by(TestExecution.started_at)))
    evidence = list(db.scalars(select(Evidence).where(Evidence.audit_run_id == audit.id).order_by(Evidence.created_at)))
    events = list(db.scalars(select(AgentEvent).where(AgentEvent.audit_run_id == audit.id).order_by(AgentEvent.occurred_at)))
    findings = list(db.scalars(select(Finding).outerjoin(
        FindingOccurrence, FindingOccurrence.finding_id == Finding.id
    ).where(
        or_(Finding.audit_run_id == audit.id, FindingOccurrence.audit_run_id == audit.id)
    ).distinct().order_by(Finding.created_at)))
    return {
        "audit": jsonable_encoder(AuditRead.model_validate(audit)),
        "target": jsonable_encoder(target) if target else None,
        "executions": [jsonable_encoder(item) for item in executions],
        "evidence": [jsonable_encoder(item) for item in evidence],
        "events": [jsonable_encoder(item) for item in events],
        "findings": [jsonable_encoder(item) for item in findings],
        "historical_data_notice": None if evidence else "No audit-linked evidence was captured by the version that created this record.",
    }


@router.get("/audits/{audit_id}/export")
async def export_audit(audit_id: str, format: str = "json", db: Session = Depends(get_db)) -> Response:
    detail = await audit_detail(audit_id, db)
    if format == "json":
        content = json.dumps(jsonable_encoder(detail), ensure_ascii=False, indent=2).encode()
        return Response(content, media_type="application/json", headers={"Content-Disposition": f'attachment; filename="audit-{audit_id}.json"'})
    if format != "pdf":
        raise HTTPException(422, "Export format must be json or pdf")
    from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
    from reportlab.lib.styles import getSampleStyleSheet  # type: ignore[import-untyped]
    from reportlab.platypus import (  # type: ignore[import-untyped]
        Paragraph,
        Preformatted,
        SimpleDocTemplate,
        Spacer,
    )

    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    document = SimpleDocTemplate(buffer, pagesize=A4, title=f"AgentSec audit {audit_id}")
    audit = detail["audit"]
    story = [Paragraph(f"AgentSec Inspector — {audit_id}", styles["Title"]), Spacer(1, 12)]
    story.append(Preformatted(json.dumps(audit, ensure_ascii=False, indent=2), styles["Code"]))
    for section in ("executions", "events", "evidence", "findings"):
        story.extend([Spacer(1, 12), Paragraph(section.title(), styles["Heading2"]), Preformatted(json.dumps(detail[section], ensure_ascii=False, indent=2)[:30_000], styles["Code"])])
    document.build(story)
    return Response(buffer.getvalue(), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="audit-{audit_id}.pdf"'})


@router.get("/attack-chain-layout/{project_id}")
async def get_attack_chain_layout(project_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    if not db.get(Project, project_id):
        raise HTTPException(404, "Project not found")
    item = db.get(AppSetting, f"attack-chain-layout:{project_id}")
    return item.value if item else {"nodes": {}}


@router.put("/attack-chain-layout/{project_id}")
async def save_attack_chain_layout(project_id: str, body: GraphLayoutUpdate, db: Session = Depends(get_db)) -> dict[str, object]:
    if not db.get(Project, project_id):
        raise HTTPException(404, "Project not found")
    key = f"attack-chain-layout:{project_id}"
    value: dict[str, object] = {"nodes": {name: position.model_dump() for name, position in body.nodes.items()}}
    item = db.get(AppSetting, key)
    if item:
        item.value = value
    else:
        db.add(AppSetting(key=key, value=value))
    db.commit()
    return value


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
