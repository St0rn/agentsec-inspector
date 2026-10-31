from __future__ import annotations

from conftest import APIClient

from agentsec.database import SessionLocal
from agentsec.models import AuditRun, AuditStatus, Finding


def make_completed_audit(project_id: str) -> str:
    with SessionLocal() as db:
        item = AuditRun(
            project_id=project_id,
            audit_type="mcp_security",
            status=AuditStatus.completed,
            passive=True,
        )
        db.add(item)
        db.commit()
        return item.id


def test_deleting_audit_requires_confirmation_and_preserves_findings(
    client: APIClient, headers: dict[str, str], project: dict[str, object]
) -> None:
    audit_id = make_completed_audit(str(project["id"]))
    with SessionLocal() as db:
        finding = Finding(
            project_id=str(project["id"]),
            audit_run_id=audit_id,
            title="Historical observation",
            description="Previously observed",
            component="read_note",
            classification="Observation",
            severity="low",
            confidence="high",
        )
        db.add(finding)
        db.commit()
        finding_id = finding.id

    url = f"/api/v1/audits/{audit_id}"
    assert client.delete(url, headers=headers).status_code == 409
    assert client.delete(url + "?confirm_delete=true", headers=headers).status_code == 204
    assert client.get(url, headers=headers).status_code == 404
    with SessionLocal() as db:
        preserved = db.get(Finding, finding_id)
        assert preserved is not None
        assert preserved.audit_run_id is None


def test_bulk_audit_deletion_only_removes_selected_type(
    client: APIClient, headers: dict[str, str], project: dict[str, object]
) -> None:
    audit_id = make_completed_audit(str(project["id"]))
    with SessionLocal() as db:
        other = AuditRun(
            project_id=str(project["id"]),
            audit_type="prompt_injection",
            status=AuditStatus.completed,
            passive=False,
        )
        db.add(other)
        db.commit()
        other_id = other.id
    url = f"/api/v1/audits?project_id={project['id']}&audit_type=mcp_security"
    assert client.delete(url, headers=headers).status_code == 409
    response = client.delete(url + "&confirm_delete=true", headers=headers)
    assert response.status_code == 200
    assert response.json()["deleted"] >= 1
    assert client.get(f"/api/v1/audits/{audit_id}", headers=headers).status_code == 404
    assert client.get(f"/api/v1/audits/{other_id}", headers=headers).status_code == 200
