from __future__ import annotations

import hashlib
import json
import textwrap
from collections import Counter
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from fastapi.encoders import jsonable_encoder
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import (
    AgentEvent,
    AuditRun,
    Evidence,
    Finding,
    Project,
    Report,
    Target,
    TestExecution,
)

SEVERITIES = ("critical", "high", "medium", "low", "info")
SEVERITY_WEIGHTS = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
SEVERITY_COLORS = {
    "critical": "#e11d48",
    "high": "#f43f5e",
    "medium": "#f59e0b",
    "low": "#38bdf8",
    "info": "#64748b",
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "fr": {
        "confidential": "CONFIDENTIEL",
        "technical_report": "Rapport technique",
        "executive_report": "Rapport exécutif",
        "prepared_for": "Préparé pour",
        "scope": "Périmètre autorisé",
        "period": "Période",
        "generated": "Généré le",
        "contents": "Sommaire",
        "executive_summary": "Synthèse exécutive",
        "engagement": "Présentation de la mission",
        "methodology": "Méthodologie",
        "risk_overview": "Vue d’ensemble des risques",
        "finding_summary": "Tableau récapitulatif des findings",
        "audit_summary": "Audits réalisés",
        "detailed_findings": "Findings détaillés",
        "audit_results": "Résultats détaillés des audits",
        "limitations": "Limites de l’audit",
        "recommendations": "Priorités de remédiation",
        "no_findings": "Aucun finding n’est enregistré pour ce projet.",
        "no_audits": "Aucun audit n’est enregistré pour ce projet.",
        "severity": "Sévérité",
        "classification": "Classification",
        "status": "Statut",
        "confidence": "Confiance",
        "component": "Composant / cible",
        "description": "Description",
        "impact": "Impact",
        "conditions": "Conditions d’exploitation",
        "reproduction": "Étapes de reproduction",
        "observed": "Résultat observé",
        "expected": "Résultat attendu",
        "recommendation": "Recommandation",
        "references": "Références techniques",
        "evidence": "Preuves",
        "requests": "Payloads, requêtes et réponses",
        "payload": "Payload",
        "tools": "Appels d’outils observés",
        "audit": "Audit associé",
        "date": "Date",
        "target": "Cible",
        "type": "Type",
        "result": "Résultat",
        "passive": "Passif",
        "active": "Actif",
        "yes": "Oui",
        "no": "Non",
        "page": "Page",
        "of": "sur",
        "identifier": "Identifiant",
        "total_findings": "Findings",
        "total_audits": "Audits",
        "confirmed": "Confirmés",
        "remediated": "Remédiés",
        "security_indicators": "Indicateurs de sécurité",
        "frameworks": "Référentiels",
        "configuration": "Configuration et objectif de sécurité",
        "events": "Événements observables",
        "error": "Erreur",
        "none": "Non renseigné",
        "title": "Finding",
    },
    "en": {
        "confidential": "CONFIDENTIAL",
        "technical_report": "Technical report",
        "executive_report": "Executive report",
        "prepared_for": "Prepared for",
        "scope": "Authorized scope",
        "period": "Period",
        "generated": "Generated on",
        "contents": "Table of contents",
        "executive_summary": "Executive summary",
        "engagement": "Engagement overview",
        "methodology": "Methodology",
        "risk_overview": "Risk overview",
        "finding_summary": "Finding summary",
        "audit_summary": "Audits performed",
        "detailed_findings": "Detailed findings",
        "audit_results": "Detailed audit results",
        "limitations": "Audit limitations",
        "recommendations": "Remediation priorities",
        "no_findings": "No finding is recorded for this project.",
        "no_audits": "No audit is recorded for this project.",
        "severity": "Severity",
        "classification": "Classification",
        "status": "Status",
        "confidence": "Confidence",
        "component": "Component / target",
        "description": "Description",
        "impact": "Impact",
        "conditions": "Exploitation conditions",
        "reproduction": "Reproduction steps",
        "observed": "Observed result",
        "expected": "Expected result",
        "recommendation": "Recommendation",
        "references": "Technical references",
        "evidence": "Evidence",
        "requests": "Payloads, requests and responses",
        "payload": "Payload",
        "tools": "Observed tool calls",
        "audit": "Related audit",
        "date": "Date",
        "target": "Target",
        "type": "Type",
        "result": "Result",
        "passive": "Passive",
        "active": "Active",
        "yes": "Yes",
        "no": "No",
        "page": "Page",
        "of": "of",
        "identifier": "Identifier",
        "total_findings": "Findings",
        "total_audits": "Audits",
        "confirmed": "Confirmed",
        "remediated": "Remediated",
        "security_indicators": "Security indicators",
        "frameworks": "Frameworks",
        "configuration": "Configuration and security objective",
        "events": "Observable events",
        "error": "Error",
        "none": "Not provided",
        "title": "Finding",
    },
}


def _iso(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    return str(value)


def _serialise(value: Any) -> Any:
    return jsonable_encoder(value)


def _tool_calls(executions: list[TestExecution], events: list[AgentEvent]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    seen: set[str] = set()
    for execution in executions:
        response = execution.response_data or {}
        candidates = response.get("tool_calls") or response.get("tools") or []
        if isinstance(candidates, dict):
            candidates = [candidates]
        if isinstance(candidates, list):
            for item in candidates:
                normalised = item if isinstance(item, dict) else {"value": item}
                key = json.dumps(normalised, sort_keys=True, ensure_ascii=False, default=str)
                if key not in seen:
                    seen.add(key)
                    calls.append(_serialise(normalised))
    for event in events:
        if "tool" not in event.event_type.lower():
            continue
        normalised = {
            "event_type": event.event_type,
            "actor": event.actor,
            "target": event.target,
            "payload": _serialise(event.payload),
            "occurred_at": _iso(event.occurred_at),
        }
        key = json.dumps(normalised, sort_keys=True, ensure_ascii=False, default=str)
        if key not in seen:
            seen.add(key)
            calls.append(normalised)
    return calls


def build_report_data(
    db: Session,
    project_id: str,
    report_type: str,
    language: str,
) -> dict[str, Any]:
    project = db.get(Project, project_id)
    if not project:
        raise ValueError("Project not found")

    findings = list(db.scalars(select(Finding).where(Finding.project_id == project_id)))
    findings.sort(
        key=lambda item: (SEVERITY_WEIGHTS.get(item.severity.value, 0), item.created_at),
        reverse=True,
    )
    audits = list(
        db.scalars(
            select(AuditRun)
            .where(AuditRun.project_id == project_id)
            .order_by(AuditRun.created_at.desc())
        )
    )
    targets = {
        item.id: item for item in db.scalars(select(Target).where(Target.project_id == project_id))
    }
    executions = list(
        db.scalars(
            select(TestExecution)
            .join(AuditRun, AuditRun.id == TestExecution.audit_run_id)
            .where(AuditRun.project_id == project_id)
            .order_by(TestExecution.started_at)
        )
    )
    evidence = list(
        db.scalars(
            select(Evidence).where(Evidence.project_id == project_id).order_by(Evidence.created_at)
        )
    )
    events = list(
        db.scalars(
            select(AgentEvent)
            .where(AgentEvent.project_id == project_id)
            .order_by(AgentEvent.occurred_at)
        )
    )

    executions_by_audit: dict[str, list[TestExecution]] = {}
    evidence_by_audit: dict[str, list[Evidence]] = {}
    evidence_by_finding: dict[str, list[Evidence]] = {}
    events_by_audit: dict[str, list[AgentEvent]] = {}
    for execution_record in executions:
        executions_by_audit.setdefault(execution_record.audit_run_id, []).append(execution_record)
    for evidence_record in evidence:
        if evidence_record.audit_run_id:
            evidence_by_audit.setdefault(evidence_record.audit_run_id, []).append(evidence_record)
        if evidence_record.finding_id:
            evidence_by_finding.setdefault(evidence_record.finding_id, []).append(evidence_record)
    for event_record in events:
        if event_record.audit_run_id:
            events_by_audit.setdefault(event_record.audit_run_id, []).append(event_record)

    audit_payloads: list[dict[str, Any]] = []
    for audit in audits:
        audit_executions = executions_by_audit.get(audit.id, [])
        audit_events = events_by_audit.get(audit.id, [])
        target = targets.get(audit.target_id or "")
        audit_payloads.append(
            {
                "id": audit.id,
                "type": audit.audit_type,
                "status": audit.status.value,
                "mode": "passive" if audit.passive else "active",
                "target": target.name if target else "",
                "target_endpoint": target.endpoint if target else "",
                "configuration": _serialise(audit.configuration),
                "summary": _serialise(audit.summary),
                "error": audit.error or "",
                "started_at": _iso(audit.started_at),
                "finished_at": _iso(audit.finished_at),
                "created_at": _iso(audit.created_at),
                "executions": [
                    {
                        "id": item.id,
                        "scenario_id": item.scenario_id,
                        "scenario_version": item.scenario_version,
                        "status": item.status,
                        "request": _serialise(item.request_data),
                        "response": _serialise(item.response_data),
                        "analysis": _serialise(item.analysis),
                        "started_at": _iso(item.started_at),
                        "finished_at": _iso(item.finished_at),
                    }
                    for item in audit_executions
                ],
                "evidence": [
                    {
                        "id": item.id,
                        "type": item.evidence_type,
                        "title": item.title,
                        "content": item.content,
                        "sha256": item.sha256,
                        "created_at": _iso(item.created_at),
                    }
                    for item in evidence_by_audit.get(audit.id, [])
                ],
                "events": [
                    {
                        "id": item.id,
                        "type": item.event_type,
                        "actor": item.actor,
                        "target": item.target or "",
                        "payload": _serialise(item.payload),
                        "duration_ms": item.duration_ms,
                        "occurred_at": _iso(item.occurred_at),
                    }
                    for item in audit_events
                ],
                "tool_calls": _tool_calls(audit_executions, audit_events),
            }
        )

    audit_map = {item["id"]: item for item in audit_payloads}
    finding_payloads: list[dict[str, Any]] = []
    for finding_record in findings:
        related_audit = audit_map.get(finding_record.audit_run_id or "")
        finding_payloads.append(
            {
                "id": finding_record.id,
                "title": finding_record.title,
                "description": finding_record.description,
                "component": finding_record.component,
                "classification": finding_record.classification,
                "severity": finding_record.severity.value,
                "confidence": finding_record.confidence,
                "impact": finding_record.impact,
                "exploitation_conditions": finding_record.exploitation_conditions,
                "reproduction_steps": finding_record.reproduction_steps,
                "observed_result": finding_record.observed_result,
                "expected_result": finding_record.expected_result,
                "recommendation": finding_record.recommendation,
                "status": finding_record.status.value,
                "frameworks": _serialise(finding_record.frameworks),
                "created_at": _iso(finding_record.created_at),
                "updated_at": _iso(finding_record.updated_at),
                "audit_id": finding_record.audit_run_id or "",
                "target": related_audit["target"] if related_audit else finding_record.component,
                "evidence": [
                    {
                        "id": record.id,
                        "type": record.evidence_type,
                        "title": record.title,
                        "content": record.content,
                        "sha256": record.sha256,
                        "created_at": _iso(record.created_at),
                    }
                    for record in evidence_by_finding.get(finding_record.id, [])
                ],
                "executions": related_audit["executions"] if related_audit else [],
                "tool_calls": related_audit["tool_calls"] if related_audit else [],
            }
        )

    severity_counts = Counter(item["severity"] for item in finding_payloads)
    status_counts = Counter(item["status"] for item in finding_payloads)
    audit_type_counts = Counter(item["type"] for item in audit_payloads)
    generated_at = datetime.now(UTC)
    methodology = (
        "Découverte passive et tests actifs explicitement autorisés. Les verdicts reposent uniquement sur les réponses, événements, appels d’outils et preuves observables conservés par AgentSec Inspector."
        if language == "fr"
        else "Passive discovery and explicitly authorized active tests. Verdicts rely only on responses, events, tool calls, and observable evidence retained by AgentSec Inspector."
    )
    limitations = (
        "Les conclusions sont limitées aux interfaces exposées, aux tests exécutés et à la télémétrie fournie par les systèmes audités. L’absence de finding ne démontre pas l’absence de vulnérabilité."
        if language == "fr"
        else "Conclusions are limited to exposed interfaces, executed tests, and telemetry supplied by the audited systems. The absence of a finding does not prove the absence of vulnerabilities."
    )
    return {
        "schema_version": "2.0",
        "project": {
            "id": project.id,
            "client_name": project.client_name,
            "engagement_name": project.engagement_name,
            "description": project.description,
            "authorized_scope": project.authorized_scope,
            "start_date": _iso(project.start_date),
            "end_date": _iso(project.end_date),
        },
        "report_type": report_type,
        "language": language,
        "generated_at": generated_at.isoformat(),
        "generated_display": generated_at.strftime("%Y-%m-%d %H:%M UTC"),
        "confidentiality": TRANSLATIONS[language]["confidential"],
        "methodology": methodology,
        "limitations": limitations,
        "translations": TRANSLATIONS[language],
        "statistics": {
            "findings": len(finding_payloads),
            "audits": len(audit_payloads),
            "confirmed": status_counts.get("Confirmed", 0),
            "remediated": status_counts.get("Remediated", 0),
            "severity": {name: severity_counts.get(name, 0) for name in SEVERITIES},
            "statuses": dict(sorted(status_counts.items())),
            "audit_types": dict(sorted(audit_type_counts.items())),
        },
        "findings": finding_payloads,
        "audits": audit_payloads,
    }


def _environment() -> Environment:
    template_root = Path(__file__).parents[1] / "templates"
    return Environment(
        loader=FileSystemLoader(template_root),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_report_html(data: dict[str, Any]) -> str:
    return _environment().get_template("report.html.j2").render(**data)


def _json_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _wrapped_markup(value: Any, width: int = 92) -> str:
    text = _json_text(value) or "—"
    lines: list[str] = []
    for original in text.splitlines() or [""]:
        lines.extend(
            textwrap.wrap(
                original,
                width=width,
                replace_whitespace=False,
                drop_whitespace=False,
                break_long_words=True,
                break_on_hyphens=False,
            )
            or [""]
        )
    return "<br/>".join(escape(line) for line in lines)


def render_report_pdf(data: dict[str, Any]) -> bytes:
    from reportlab.lib import colors  # type: ignore[import-untyped]
    from reportlab.lib.enums import TA_CENTER, TA_LEFT  # type: ignore[import-untyped]
    from reportlab.lib.fonts import addMapping  # type: ignore[import-untyped]
    from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
    from reportlab.lib.styles import (  # type: ignore[import-untyped]
        ParagraphStyle,
        getSampleStyleSheet,
    )
    from reportlab.lib.units import mm  # type: ignore[import-untyped]
    from reportlab.pdfbase import pdfmetrics  # type: ignore[import-untyped]
    from reportlab.pdfbase.ttfonts import TTFont  # type: ignore[import-untyped]
    from reportlab.platypus import (  # type: ignore[import-untyped]
        BaseDocTemplate,
        Flowable,
        Frame,
        HRFlowable,
        KeepTogether,
        NextPageTemplate,
        PageBreak,
        PageTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.platypus.tableofcontents import TableOfContents  # type: ignore[import-untyped]

    try:
        pdfmetrics.registerFont(TTFont("AgentSecSans", "Vera.ttf"))
        pdfmetrics.registerFont(TTFont("AgentSecSans-Bold", "VeraBd.ttf"))
        addMapping("AgentSecSans", 0, 0, "AgentSecSans")
        addMapping("AgentSecSans", 1, 0, "AgentSecSans-Bold")
        font, bold = "AgentSecSans", "AgentSecSans-Bold"
    except Exception:  # pragma: no cover
        font, bold = "Helvetica", "Helvetica-Bold"

    navy = colors.HexColor("#07111f")
    navy_2 = colors.HexColor("#0b1b31")
    cyan = colors.HexColor("#22d3ee")
    electric = colors.HexColor("#2f7bff")
    slate = colors.HexColor("#475569")
    line = colors.HexColor("#cbd5e1")
    t = data["translations"]
    project = data["project"]
    buffer = BytesIO()

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "ReportTitle",
            fontName=bold,
            fontSize=28,
            leading=33,
            textColor=colors.white,
            alignment=TA_LEFT,
            spaceAfter=7 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "H1A",
            fontName=bold,
            fontSize=18,
            leading=22,
            textColor=navy,
            spaceBefore=6 * mm,
            spaceAfter=4 * mm,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            "H2A",
            fontName=bold,
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#075985"),
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            "BodyA",
            fontName=font,
            fontSize=9.2,
            leading=13.2,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=2.5 * mm,
        )
    )
    styles.add(
        ParagraphStyle("SmallA", parent=styles["BodyA"], fontSize=7.5, leading=10, textColor=slate)
    )
    styles.add(
        ParagraphStyle(
            "CodeA",
            parent=styles["BodyA"],
            fontName=font,
            fontSize=7.2,
            leading=10,
            textColor=colors.HexColor("#dbeafe"),
            backColor=navy,
            borderPadding=7,
            borderColor=colors.HexColor("#1e3a5f"),
            borderWidth=0.5,
            borderRadius=3,
            spaceBefore=1 * mm,
            spaceAfter=3 * mm,
            splitLongWords=True,
        )
    )
    styles.add(
        ParagraphStyle(
            "Metric",
            fontName=bold,
            fontSize=18,
            leading=21,
            textColor=electric,
            alignment=TA_CENTER,
        )
    )
    styles.add(
        ParagraphStyle(
            "MetricLabel",
            fontName=font,
            fontSize=7,
            leading=9,
            textColor=slate,
            alignment=TA_CENTER,
        )
    )

    class AgentSecDocTemplate(BaseDocTemplate):
        def afterFlowable(self, flowable: Flowable) -> None:
            if isinstance(flowable, Paragraph):
                style_name = flowable.style.name
                if style_name == "H1A":
                    key = f"h1-{self.page}-{flowable.getPlainText()}"
                    self.canv.bookmarkPage(key)
                    self.canv.addOutlineEntry(flowable.getPlainText(), key, level=0)
                    self.notify("TOCEntry", (0, flowable.getPlainText(), self.page, key))

    doc = AgentSecDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=17 * mm,
        rightMargin=17 * mm,
        topMargin=22 * mm,
        bottomMargin=18 * mm,
        title=f"AgentSec Inspector — {project['engagement_name']}",
        author="AgentSec Inspector",
        subject=t["technical_report"]
        if data["report_type"] == "technical"
        else t["executive_report"],
    )
    body_frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="body",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    cover_frame = Frame(0, 0, A4[0], A4[1], id="cover", showBoundary=0)

    def cover_page(canvas: Any, _doc: Any) -> None:
        width, height = A4
        canvas.saveState()
        canvas.setFillColor(navy)
        canvas.rect(0, 0, width, height, fill=1, stroke=0)
        canvas.setFillColor(navy_2)
        canvas.circle(width * 0.86, height * 0.84, 74 * mm, fill=1, stroke=0)
        canvas.setStrokeColor(cyan)
        canvas.setLineWidth(1.5)
        canvas.circle(width * 0.86, height * 0.84, 54 * mm, fill=0, stroke=1)
        canvas.setFillColor(cyan)
        canvas.roundRect(18 * mm, height - 28 * mm, 10 * mm, 10 * mm, 2 * mm, fill=1, stroke=0)
        canvas.setFillColor(navy)
        canvas.setFont(bold, 12)
        canvas.drawCentredString(23 * mm, height - 24.2 * mm, "A")
        canvas.setFillColor(colors.white)
        canvas.setFont(bold, 12)
        canvas.drawString(32 * mm, height - 24.7 * mm, "AGENTSEC INSPECTOR")
        canvas.setFillColor(cyan)
        canvas.setFont(bold, 8)
        canvas.drawRightString(width - 18 * mm, height - 24.5 * mm, data["confidentiality"])
        canvas.restoreState()

    def body_page(canvas: Any, current_doc: Any) -> None:
        width, height = A4
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#dbe4ee"))
        canvas.setLineWidth(0.5)
        canvas.line(17 * mm, height - 15 * mm, width - 17 * mm, height - 15 * mm)
        canvas.setFont(bold, 7.5)
        canvas.setFillColor(navy)
        canvas.drawString(17 * mm, height - 11 * mm, "AGENTSEC INSPECTOR")
        canvas.setFont(font, 7)
        canvas.setFillColor(slate)
        canvas.drawRightString(width - 17 * mm, height - 11 * mm, project["engagement_name"][:70])
        canvas.line(17 * mm, 12 * mm, width - 17 * mm, 12 * mm)
        canvas.drawString(17 * mm, 7.5 * mm, data["confidentiality"])
        canvas.drawCentredString(width / 2, 7.5 * mm, project["client_name"][:70])
        canvas.drawRightString(width - 17 * mm, 7.5 * mm, f"{t['page']} {current_doc.page}")
        canvas.restoreState()

    doc.addPageTemplates(
        [
            PageTemplate(id="Cover", frames=[cover_frame], onPage=cover_page),
            PageTemplate(id="Body", frames=[body_frame], onPage=body_page),
        ]
    )

    def p(value: Any, style: str = "BodyA") -> Paragraph:
        text = str(value).strip() if value is not None else ""
        return Paragraph(escape(text or t["none"]).replace("\n", "<br/>"), styles[style])

    def code(value: Any) -> Paragraph:
        return Paragraph(_wrapped_markup(value), styles["CodeA"])

    def label_value(label: str, value: Any) -> list[Flowable]:
        if value in (None, "", [], {}):
            return []
        return [Paragraph(escape(label), styles["H2A"]), p(value)]

    def section(title: str) -> Paragraph:
        return Paragraph(escape(title), styles["H1A"])

    def table(rows: list[list[Any]], widths: list[float] | None = None) -> Table:
        converted = [
            [cell if isinstance(cell, Flowable) else p(cell, "SmallA") for cell in row]
            for row in rows
        ]
        result = Table(converted, colWidths=widths, repeatRows=1, hAlign="LEFT", splitByRow=1)
        result.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), navy),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), bold),
                    ("FONTSIZE", (0, 0), (-1, 0), 7.5),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.35, line),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#f8fafc")],
                    ),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        return result

    report_label = (
        t["technical_report"] if data["report_type"] == "technical" else t["executive_report"]
    )
    story: list[Flowable] = [
        Spacer(1, 52 * mm),
        Paragraph(escape(report_label.upper()), styles["SmallA"]),
        Paragraph(escape(project["engagement_name"]), styles["ReportTitle"]),
        HRFlowable(width="42%", color=cyan, thickness=2, hAlign="LEFT", spaceAfter=7 * mm),
        Paragraph(
            f"<font color='#22d3ee'>{escape(t['prepared_for'])}</font><br/><font size='16'>{escape(project['client_name'])}</font>",
            ParagraphStyle(
                "CoverClient",
                parent=styles["BodyA"],
                fontName=bold,
                fontSize=10,
                leading=20,
                textColor=colors.white,
            ),
        ),
        Spacer(1, 15 * mm),
        Paragraph(
            f"<font color='#94a3b8'>{escape(t['scope'])}</font><br/>{escape(project['authorized_scope'] or t['none'])}",
            ParagraphStyle(
                "CoverMeta", parent=styles["BodyA"], fontSize=9, leading=14, textColor=colors.white
            ),
        ),
        Spacer(1, 5 * mm),
        Paragraph(
            f"<font color='#94a3b8'>{escape(t['period'])}</font><br/>{escape(project['start_date'] or '—')} — {escape(project['end_date'] or '—')}<br/><br/><font color='#94a3b8'>{escape(t['generated'])}</font><br/>{escape(data['generated_display'])}",
            ParagraphStyle(
                "CoverMeta2", parent=styles["BodyA"], fontSize=9, leading=14, textColor=colors.white
            ),
        ),
        NextPageTemplate("Body"),
        PageBreak(),
        section(t["contents"]),
    ]
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOC1", fontName=bold, fontSize=10, leading=15, leftIndent=0, textColor=navy
        ),
        ParagraphStyle(
            "TOC2", fontName=font, fontSize=8, leading=12, leftIndent=10, textColor=slate
        ),
    ]
    story.extend([toc, PageBreak(), section(t["executive_summary"])])

    metrics = [
        (data["statistics"]["findings"], t["total_findings"]),
        (data["statistics"]["audits"], t["total_audits"]),
        (data["statistics"]["confirmed"], t["confirmed"]),
        (data["statistics"]["remediated"], t["remediated"]),
    ]
    metric_table = Table(
        [
            [Paragraph(str(value), styles["Metric"]) for value, _ in metrics],
            [Paragraph(label, styles["MetricLabel"]) for _, label in metrics],
        ],
        colWidths=[doc.width / 4] * 4,
    )
    metric_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f9ff")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#bae6fd")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bae6fd")),
                ("TOPPADDING", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
            ]
        )
    )
    story.extend([metric_table, Spacer(1, 5 * mm), p(project["description"] or t["none"])])
    story.extend(
        [
            section(t["engagement"]),
            p(project["description"]),
            Paragraph(escape(t["scope"]), styles["H2A"]),
            p(project["authorized_scope"]),
        ]
    )
    story.extend([section(t["methodology"]), p(data["methodology"]), section(t["risk_overview"])])
    severity_rows: list[list[Any]] = [[t["severity"], t["total_findings"]]]
    for severity in SEVERITIES:
        severity_rows.append([severity.upper(), str(data["statistics"]["severity"][severity])])
    story.append(table(severity_rows, [doc.width * 0.7, doc.width * 0.3]))

    story.append(section(t["finding_summary"]))
    if data["findings"]:
        rows = [[t["identifier"], t["severity"], t["status"], t["title"]]]
        for finding in data["findings"]:
            rows.append(
                [finding["id"], finding["severity"].upper(), finding["status"], finding["title"]]
            )
        story.append(table(rows, [32 * mm, 22 * mm, 29 * mm, doc.width - 83 * mm]))
    else:
        story.append(p(t["no_findings"]))

    story.append(section(t["audit_summary"]))
    if data["audits"]:
        rows = [[t["date"], t["type"], t["target"], t["result"]]]
        for audit in data["audits"]:
            rows.append(
                [audit["created_at"][:19], audit["type"], audit["target"] or "—", audit["status"]]
            )
        story.append(table(rows, [31 * mm, 42 * mm, 55 * mm, doc.width - 128 * mm]))
    else:
        story.append(p(t["no_audits"]))

    story.extend([PageBreak(), section(t["detailed_findings"])])
    if not data["findings"]:
        story.append(p(t["no_findings"]))
    for index, finding in enumerate(data["findings"], start=1):
        if index > 1:
            story.append(PageBreak())
        severity_color = colors.HexColor(SEVERITY_COLORS.get(finding["severity"], "#64748b"))
        heading = Table(
            [
                [
                    Paragraph(
                        f"<b>{index:02d}</b>",
                        ParagraphStyle(
                            "FindingIndex",
                            parent=styles["H1A"],
                            textColor=colors.white,
                            alignment=TA_CENTER,
                        ),
                    ),
                    Paragraph(escape(finding["title"]), styles["H1A"]),
                ]
            ],
            colWidths=[14 * mm, doc.width - 14 * mm],
        )
        heading.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), severity_color),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.extend(
            [
                heading,
                Spacer(1, 2 * mm),
                table(
                    [
                        [t["severity"], t["classification"], t["status"], t["confidence"]],
                        [
                            finding["severity"].upper(),
                            finding["classification"],
                            finding["status"],
                            finding["confidence"],
                        ],
                        [t["identifier"], t["component"], t["target"], t["date"]],
                        [
                            finding["id"],
                            finding["component"],
                            finding["target"],
                            finding["created_at"][:19],
                        ],
                    ],
                    [doc.width * 0.22, doc.width * 0.28, doc.width * 0.22, doc.width * 0.28],
                ),
            ]
        )
        story.extend(label_value(t["description"], finding["description"]))
        story.extend(label_value(t["impact"], finding["impact"]))
        story.extend(label_value(t["conditions"], finding["exploitation_conditions"]))
        story.extend(label_value(t["reproduction"], finding["reproduction_steps"]))
        story.extend(label_value(t["observed"], finding["observed_result"]))
        story.extend(label_value(t["expected"], finding["expected_result"]))
        story.extend(label_value(t["recommendation"], finding["recommendation"]))
        if finding["frameworks"]:
            story.extend(
                [Paragraph(escape(t["frameworks"]), styles["H2A"]), code(finding["frameworks"])]
            )
        if finding["evidence"]:
            story.append(Paragraph(escape(t["evidence"]), styles["H2A"]))
            for record in finding["evidence"]:
                story.extend(
                    [
                        p(
                            f"{record['title']} · {record['type']} · SHA-256 {record['sha256']}",
                            "SmallA",
                        ),
                        code(record["content"]),
                    ]
                )
        if finding["executions"]:
            story.append(Paragraph(escape(t["requests"]), styles["H2A"]))
            for execution in finding["executions"]:
                story.append(
                    p(
                        f"{execution['scenario_id']}@{execution['scenario_version']} — {execution['status']}",
                        "SmallA",
                    )
                )
                turns = execution["request"].get("turns", [])
                if not turns and execution["request"].get("messages"):
                    turns = [
                        {
                            "step": 1,
                            "exact_payload_sent": {"messages": execution["request"]["messages"]},
                        }
                    ]
                for turn in turns:
                    story.extend(
                        [
                            Paragraph(escape(t["payload"]), styles["H2A"]),
                            code(turn.get("exact_payload_sent", {})),
                        ]
                    )
                story.append(
                    code({"response": execution["response"], "analysis": execution["analysis"]})
                )
        if finding["tool_calls"]:
            story.extend(
                [Paragraph(escape(t["tools"]), styles["H2A"]), code(finding["tool_calls"])]
            )

    if data["report_type"] == "technical":
        story.extend([PageBreak(), section(t["audit_results"])])
        if not data["audits"]:
            story.append(p(t["no_audits"]))
        for audit in data["audits"]:
            story.extend(
                [
                    Paragraph(escape(f"{audit['type']} — {audit['id']}"), styles["H2A"]),
                    table(
                        [
                            [t["target"], t["result"], t["type"], t["date"]],
                            [
                                audit["target"] or "—",
                                audit["status"],
                                t[audit["mode"]],
                                audit["created_at"][:19],
                            ],
                        ],
                        [doc.width * 0.32, doc.width * 0.2, doc.width * 0.18, doc.width * 0.3],
                    ),
                ]
            )
            if audit["configuration"]:
                story.extend(
                    [
                        Paragraph(escape(t["configuration"]), styles["H2A"]),
                        code(audit["configuration"]),
                    ]
                )
            if audit["summary"]:
                story.extend(
                    [
                        Paragraph(escape(t["executive_summary"]), styles["H2A"]),
                        code(audit["summary"]),
                    ]
                )
            if audit["error"]:
                story.extend([Paragraph(escape(t["error"]), styles["H2A"]), code(audit["error"])])
            if audit["executions"]:
                story.append(Paragraph(escape(t["requests"]), styles["H2A"]))
                for execution in audit["executions"]:
                    story.append(p(f"{execution['scenario_id']} — {execution['status']}", "SmallA"))
                    turns = execution["request"].get("turns", [])
                    if not turns and execution["request"].get("messages"):
                        turns = [
                            {
                                "step": 1,
                                "exact_payload_sent": {
                                    "messages": execution["request"]["messages"]
                                },
                            }
                        ]
                    for turn in turns:
                        story.extend(
                            [
                                Paragraph(escape(t["payload"]), styles["H2A"]),
                                code(turn.get("exact_payload_sent", {})),
                            ]
                        )
                    story.append(
                        code({"response": execution["response"], "analysis": execution["analysis"]})
                    )
            if audit["tool_calls"]:
                story.extend(
                    [Paragraph(escape(t["tools"]), styles["H2A"]), code(audit["tool_calls"])]
                )
            if audit["events"]:
                story.extend([Paragraph(escape(t["events"]), styles["H2A"]), code(audit["events"])])
            if audit["evidence"]:
                story.append(Paragraph(escape(t["evidence"]), styles["H2A"]))
                for record in audit["evidence"]:
                    story.extend(
                        [
                            p(
                                f"{record['title']} · {record['type']} · SHA-256 {record['sha256']}",
                                "SmallA",
                            ),
                            code(record["content"]),
                        ]
                    )
            story.append(Spacer(1, 3 * mm))

    story.extend([PageBreak(), section(t["limitations"]), p(data["limitations"])])
    if data["findings"]:
        story.append(section(t["recommendations"]))
        for finding in data["findings"]:
            if finding["recommendation"]:
                story.append(
                    KeepTogether(
                        [
                            Paragraph(escape(finding["title"]), styles["H2A"]),
                            p(finding["recommendation"]),
                        ]
                    )
                )

    doc.multiBuild(story)
    return buffer.getvalue()


def preview_report(db: Session, project_id: str, report_type: str, language: str) -> str:
    return render_report_html(build_report_data(db, project_id, report_type, language))


def generate_report(
    db: Session,
    settings: Settings,
    project_id: str,
    report_type: str,
    language: str,
    output_format: str,
    template_name: str,
) -> Report:
    data = build_report_data(db, project_id, report_type, language)
    output_dir = settings.data_dir / "reports" / project_id
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    stem = f"agentsec-{report_type}-{language}-{template_name}-{stamp}"
    if output_format == "json":
        content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    elif output_format == "html":
        content = render_report_html(data).encode("utf-8")
    elif output_format == "pdf":
        content = render_report_pdf(data)
    else:
        raise ValueError("Unsupported report format")
    output = output_dir / f"{stem}.{output_format}"
    output.write_bytes(content)
    report = Report(
        project_id=project_id,
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
