from __future__ import annotations

from conftest import APIClient
from sqlalchemy import text

from agentsec.database import engine, migrate_db


def test_html_and_json_report_generation(
    client: APIClient, headers: dict[str, str], project: dict[str, object]
) -> None:
    for output_format in ("html", "json", "pdf"):
        response = client.post(
            "/api/v1/reports",
            headers=headers,
            json={
                "project_id": project["id"],
                "report_type": "technical",
                "language": "fr",
                "format": output_format,
                "template_name": "default",
            },
        )
        assert response.status_code == 201, response.text
        payload = response.json()
        assert len(payload["sha256"]) == 64
        download = client.get(f"/api/v1/reports/{payload['id']}/download", headers=headers)
        assert download.status_code == 200
        assert download.content
        if output_format == "pdf":
            assert download.content.startswith(b"%PDF")


def test_backup_and_integrity(
    client: APIClient, headers: dict[str, str], project: dict[str, object]
) -> None:
    integrity = client.get("/api/v1/integrity", headers=headers)
    assert integrity.status_code == 200
    assert integrity.json()["database"] == "ok"
    backup = client.post("/api/v1/backups", headers=headers)
    assert backup.status_code == 201
    assert len(backup.json()["sha256"]) == 64


def test_alembic_migration_reaches_head() -> None:
    migrate_db()
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0001_initial"
        )
