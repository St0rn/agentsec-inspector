from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    AuditRun,
    Evidence,
    Finding,
    FindingHistory,
    FindingOccurrence,
    Project,
    TestExecution,
)
from ..schemas import FindingCreate, FindingRead, FindingUpdate

router = APIRouter(tags=["findings"])


@router.get("/findings", response_model=list[FindingRead])
async def list_findings(
    project_id: str | None = None, db: Session = Depends(get_db)
) -> list[Finding]:
    statement = select(Finding).order_by(Finding.created_at.desc())
    if project_id:
        statement = statement.where(Finding.project_id == project_id)
    return list(db.scalars(statement))


@router.post("/findings", response_model=FindingRead, status_code=201)
async def create_finding(body: FindingCreate, db: Session = Depends(get_db)) -> Finding:
    if not db.get(Project, body.project_id):
        raise HTTPException(404, "Project not found")
    finding = Finding(**body.model_dump())
    db.add(finding)
    db.flush()
    db.add(FindingHistory(finding_id=finding.id, changes={"created": body.model_dump(mode="json")}))
    db.commit()
    db.refresh(finding)
    return finding


@router.put("/findings/{finding_id}", response_model=FindingRead)
async def update_finding(
    finding_id: str, body: FindingUpdate, db: Session = Depends(get_db)
) -> Finding:
    finding = db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(404, "Finding not found")
    updates = body.model_dump(exclude_unset=True)
    changes: dict[str, object] = {}
    for key, value in updates.items():
        old = getattr(finding, key)
        if old != value:
            changes[key] = {
                "from": getattr(old, "value", old),
                "to": getattr(value, "value", value),
            }
            setattr(finding, key, value)
    if changes:
        db.add(FindingHistory(finding_id=finding.id, changes=changes))
    db.commit()
    db.refresh(finding)
    return finding


@router.get("/findings/{finding_id}/detail")
async def finding_detail(finding_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    finding = db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(404, "Finding not found")
    audit = db.get(AuditRun, finding.audit_run_id) if finding.audit_run_id else None
    executions = (
        list(
            db.scalars(
                select(TestExecution)
                .where(TestExecution.audit_run_id == finding.audit_run_id)
                .order_by(TestExecution.started_at)
            )
        )
        if finding.audit_run_id
        else []
    )
    evidence = list(
        db.scalars(
            select(Evidence)
            .where(Evidence.finding_id == finding.id)
            .order_by(Evidence.created_at)
        )
    )
    occurrences = list(
        db.scalars(
            select(FindingOccurrence)
            .where(FindingOccurrence.finding_id == finding.id)
            .order_by(FindingOccurrence.observed_at.desc())
        )
    )
    return {
        "occurrences": [jsonable_encoder(item) for item in occurrences],
        "finding": jsonable_encoder(FindingRead.model_validate(finding)),
        "audit": jsonable_encoder(audit) if audit else None,
        "executions": [jsonable_encoder(item) for item in executions],
        "evidence": [jsonable_encoder(item) for item in evidence],
    }


@router.get("/findings/{finding_id}/history")
async def finding_history(
    finding_id: str, db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    if not db.get(Finding, finding_id):
        raise HTTPException(404, "Finding not found")
    rows = db.scalars(
        select(FindingHistory)
        .where(FindingHistory.finding_id == finding_id)
        .order_by(FindingHistory.changed_at.desc())
    )
    return [
        {
            "id": row.id,
            "changed_at": row.changed_at,
            "changed_by": row.changed_by,
            "changes": row.changes,
        }
        for row in rows
    ]


@router.delete("/findings/{finding_id}", status_code=204)
async def delete_finding(
    finding_id: str, confirm_delete: bool = False, db: Session = Depends(get_db)
) -> Response:
    if not confirm_delete:
        raise HTTPException(409, "Finding deletion requires explicit confirmation")
    finding = db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(404, "Finding not found")
    db.delete(finding)
    db.commit()
    return Response(status_code=204)
