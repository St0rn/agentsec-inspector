from __future__ import annotations

import hashlib
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import AuditRun, Connector, Finding, Project, Report
from ..schemas import DashboardRead, ReportRequest
from ..services.reports import generate_report, preview_report

router = APIRouter(tags=["system"])


@router.get("/dashboard", response_model=DashboardRead)
async def dashboard(db: Session = Depends(get_db)) -> dict[str, object]:
    severity = {
        str(key.value): count
        for key, count in db.execute(
            select(Finding.severity, func.count()).group_by(Finding.severity)
        )
    }
    audit_status = {
        str(key.value): count
        for key, count in db.execute(
            select(AuditRun.status, func.count()).group_by(AuditRun.status)
        )
    }
    connector_status = {
        str(key): count
        for key, count in db.execute(
            select(Connector.last_status, func.count()).group_by(Connector.last_status)
        )
    }
    recent = list(db.scalars(select(AuditRun).order_by(AuditRun.created_at.desc()).limit(8)))
    return {
        "projects": db.scalar(select(func.count(Project.id))) or 0,
        "audits": db.scalar(select(func.count(AuditRun.id))) or 0,
        "findings": db.scalar(select(func.count(Finding.id))) or 0,
        "severity": severity,
        "audit_status": audit_status,
        "connector_status": connector_status,
        "recent_audits": recent,
    }


@router.post("/reports", status_code=201)
async def create_report(body: ReportRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        report = generate_report(
            db,
            get_settings(),
            project_id=body.project_id,
            report_type=body.report_type,
            language=body.language,
            output_format=body.format,
            template_name=body.template_name,
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {
        "id": report.id,
        "project_id": report.project_id,
        "report_type": report.report_type,
        "format": report.format,
        "language": report.language,
        "template_name": report.template_name,
        "filename": Path(report.path).name,
        "size_bytes": Path(report.path).stat().st_size,
        "sha256": report.sha256,
        "created_at": report.created_at,
    }


@router.post("/reports/preview")
async def report_preview(body: ReportRequest, db: Session = Depends(get_db)) -> Response:
    try:
        html = preview_report(db, body.project_id, body.report_type, body.language)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return Response(
        html,
        media_type="text/html",
        headers={
            "Content-Disposition": "inline; filename=agentsec-report-preview.html",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src data:",
        },
    )


@router.get("/reports")
async def list_reports(
    project_id: str | None = None, db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    statement = select(Report).order_by(Report.created_at.desc())
    if project_id:
        statement = statement.where(Report.project_id == project_id)
    return [
        {
            "id": row.id,
            "project_id": row.project_id,
            "report_type": row.report_type,
            "language": row.language,
            "format": row.format,
            "template_name": row.template_name,
            "filename": Path(row.path).name,
            "size_bytes": Path(row.path).stat().st_size if Path(row.path).is_file() else 0,
            "sha256": row.sha256,
            "created_at": row.created_at,
        }
        for row in db.scalars(statement)
    ]


@router.get("/reports/{report_id}/download")
async def download_report(report_id: str, db: Session = Depends(get_db)) -> Response:
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    path = Path(report.path).resolve()
    root = (get_settings().data_dir / "reports").resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise HTTPException(404, "Report file is unavailable")
    media = {"pdf": "application/pdf", "json": "application/json", "html": "text/html"}[
        report.format
    ]
    if path.stat().st_size > 50_000_000:
        raise HTTPException(413, "Report exceeds the download size limit")
    return Response(
        content=path.read_bytes(),
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{path.name}"'},
    )


@router.post("/backups", status_code=201)
async def backup_database() -> dict[str, str]:
    settings = get_settings()
    if not settings.db_url.startswith("sqlite:///"):
        raise HTTPException(501, "Online backup currently supports SQLite only")
    source = Path(settings.db_url.removeprefix("sqlite:///"))
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    destination = settings.data_dir / "backups" / f"agentsec-{timestamp}.db"
    with sqlite3.connect(source) as src, sqlite3.connect(destination) as dst:
        src.backup(dst)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    return {"path": str(destination), "sha256": digest}


@router.get("/integrity")
async def integrity_check(db: Session = Depends(get_db)) -> dict[str, object]:
    result = db.execute(select(func.count(Project.id))).scalar_one()
    usage = shutil.disk_usage(get_settings().data_dir)
    return {
        "database": "ok",
        "project_count": result,
        "data_directory_writable": os_access(get_settings().data_dir),
        "free_bytes": usage.free,
    }


def os_access(path: Path) -> bool:
    import os

    return os.access(path, os.W_OK | os.R_OK)
