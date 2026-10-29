from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import AuditRun, Finding, Project, Report


def generate_report(
    db: Session,
    settings: Settings,
    project_id: str,
    report_type: str,
    language: str,
    output_format: str,
    template_name: str,
) -> Report:
    project = db.get(Project, project_id)
    if not project:
        raise ValueError("Project not found")
    findings = list(
        db.scalars(
            select(Finding)
            .where(Finding.project_id == project_id)
            .order_by(Finding.severity.desc())
        )
    )
    audits = list(
        db.scalars(
            select(AuditRun)
            .where(AuditRun.project_id == project_id)
            .order_by(AuditRun.created_at.desc())
        )
    )
    data: dict[str, Any] = {
        "project": {
            "id": project.id,
            "client_name": project.client_name,
            "engagement_name": project.engagement_name,
            "description": project.description,
            "authorized_scope": project.authorized_scope,
            "start_date": str(project.start_date or ""),
            "end_date": str(project.end_date or ""),
        },
        "report_type": report_type,
        "language": language,
        "methodology": "Passive discovery and explicitly authorised active tests; observable evidence only.",
        "limitations": "Results are limited to exposed interfaces and telemetry supplied by the audited systems.",
        "audits": [
            {
                "id": item.id,
                "type": item.audit_type,
                "status": item.status.value,
                "summary": item.summary,
                "created_at": item.created_at.isoformat(),
            }
            for item in audits
        ],
        "findings": [
            {
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "component": item.component,
                "classification": item.classification,
                "severity": item.severity.value,
                "confidence": item.confidence,
                "impact": item.impact,
                "recommendation": item.recommendation,
                "status": item.status.value,
                "frameworks": item.frameworks,
            }
            for item in findings
        ],
    }
    output_dir = settings.data_dir / "reports" / project.id
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{report_type}-{language}-{template_name}"
    if output_format == "json":
        content = json.dumps(data, ensure_ascii=False, indent=2).encode()
        output = output_dir / f"{stem}.json"
        output.write_bytes(content)
    else:
        template_root = Path(__file__).parents[1] / "templates"
        env = Environment(
            loader=FileSystemLoader(template_root), autoescape=select_autoescape(["html", "xml"])
        )
        html = env.get_template("report.html.j2").render(**data)
        if output_format == "html":
            content = html.encode()
            output = output_dir / f"{stem}.html"
            output.write_bytes(content)
        elif output_format == "pdf":
            from reportlab.lib.enums import TA_CENTER  # type: ignore[import-untyped]
            from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
            from reportlab.lib.styles import (  # type: ignore[import-untyped]
                ParagraphStyle,
                getSampleStyleSheet,
            )
            from reportlab.lib.units import mm  # type: ignore[import-untyped]
            from reportlab.platypus import (  # type: ignore[import-untyped]
                Paragraph,
                SimpleDocTemplate,
                Spacer,
            )

            output = output_dir / f"{stem}.pdf"
            buffer = BytesIO()
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "AgentSecTitle", parent=styles["Title"], textColor="#075985", alignment=TA_CENTER
            )
            document = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=18 * mm,
                leftMargin=18 * mm,
                topMargin=18 * mm,
                bottomMargin=18 * mm,
                title=f"AgentSec - {project.engagement_name}",
            )
            story = [
                Paragraph(f"AgentSec Inspector - {escape(project.engagement_name)}", title_style),
                Spacer(1, 6 * mm),
                Paragraph(escape(project.client_name), styles["Heading2"]),
                Paragraph(
                    f"<b>{'Périmètre' if language == 'fr' else 'Scope'}:</b> {escape(project.authorized_scope)}",
                    styles["BodyText"],
                ),
                Spacer(1, 4 * mm),
                Paragraph("Résultats" if language == "fr" else "Results", styles["Heading1"]),
            ]
            for finding in findings:
                story.extend(
                    [
                        Paragraph(escape(finding.title), styles["Heading2"]),
                        Paragraph(
                            escape(
                                f"{finding.severity.value.upper()} - {finding.classification} - {finding.status.value}"
                            ),
                            styles["BodyText"],
                        ),
                        Paragraph(escape(finding.description), styles["BodyText"]),
                        Paragraph(
                            f"<b>{'Recommandation' if language == 'fr' else 'Recommendation'}:</b> {escape(finding.recommendation)}",
                            styles["BodyText"],
                        ),
                        Spacer(1, 3 * mm),
                    ]
                )
            story.extend(
                [
                    Paragraph("Limites" if language == "fr" else "Limitations", styles["Heading1"]),
                    Paragraph(escape(data["limitations"]), styles["BodyText"]),
                ]
            )
            document.build(story)
            content = buffer.getvalue()
            output.write_bytes(content)
        else:
            raise ValueError("Unsupported report format")
    report = Report(
        project_id=project.id,
        report_type=report_type,
        language=language,
        format=output_format,
        template_name=template_name,
        path=str(output),
        sha256=hashlib.sha256(content).hexdigest(),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
