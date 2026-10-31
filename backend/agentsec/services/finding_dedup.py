"""Evidence-based finding upserts, scoped to the exact target and finding rule."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import AuditRun, Finding, FindingHistory, FindingOccurrence, FindingStatus, Severity


def finding_fingerprint(audit: AuditRun, rule: str, component: str) -> str:
    """Never key on a title alone: target, rule and component must all match."""
    parts = [audit.project_id, audit.target_id or "", rule.strip().casefold(), component.strip().casefold()]
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()


def record_finding(
    db: Session,
    audit: AuditRun,
    *,
    rule: str,
    component: str,
    title: str,
    identity_component: str | None = None,
    description: str,
    classification: str,
    severity: Severity,
    confidence: str,
    observed_result: str,
    recommendation: str,
    **details: Any,
) -> Finding:
    """Create one finding per target/rule/component and link every distinct audit.

    The unique database constraint is authoritative under concurrent audit jobs.
    Separate occurrence rows preserve independently verifiable audit references.
    """
    fingerprint = finding_fingerprint(audit, rule, identity_component or component)
    finding = db.scalar(
        select(Finding).where(Finding.project_id == audit.project_id, Finding.fingerprint == fingerprint)
    )
    if finding is None:
        try:
            with db.begin_nested():
                finding = Finding(
                    project_id=audit.project_id,
                    audit_run_id=audit.id,
                    target_id=audit.target_id,
                    fingerprint=fingerprint,
                    occurrence_count=0,
                    title=title,
                    description=description,
                    component=component,
                    classification=classification,
                    severity=severity,
                    confidence=confidence,
                    observed_result=observed_result,
                    recommendation=recommendation,
                    **details,
                )
                db.add(finding)
                db.flush()
        except IntegrityError:
            finding = db.scalar(
                select(Finding).where(
                    Finding.project_id == audit.project_id, Finding.fingerprint == fingerprint
                )
            )
            if finding is None:
                raise
    assert finding is not None
    existed = db.scalar(
        select(FindingOccurrence).where(
            FindingOccurrence.finding_id == finding.id,
            FindingOccurrence.audit_run_id == audit.id,
        )
    )
    if existed is not None:
        return finding
    digest = hashlib.sha256(observed_result.encode()).hexdigest()
    try:
        with db.begin_nested():
            db.add(FindingOccurrence(
                finding_id=finding.id, audit_run_id=audit.id, evidence_sha256=digest,
            ))
            db.flush()
    except IntegrityError:
        # The same audit has already been recorded concurrently.
        return finding
    finding.occurrence_count += 1
    finding.last_seen = datetime.now(UTC)
    if finding.occurrence_count == 1:
        finding.first_seen = finding.last_seen
    finding.observed_result = observed_result[:30_000]
    if finding.status == FindingStatus.remediated:
        finding.status = FindingStatus.open
    db.add(FindingHistory(
        finding_id=finding.id,
        changes={"occurrence": {"audit_run_id": audit.id, "evidence_sha256": digest}},
    ))
    db.flush()
    return finding
