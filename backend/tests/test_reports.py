from __future__ import annotations

import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config
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
            == "0002_audit_evidence"
        )


def test_v101_database_migration_preserves_existing_audits_and_scenarios(tmp_path: Path) -> None:
    database = tmp_path / "legacy.db"
    with sqlite3.connect(database) as connection:
        connection.executescript(
            """
            CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY);
            INSERT INTO alembic_version VALUES ('0001_initial');
            CREATE TABLE audit_runs (id VARCHAR(36) PRIMARY KEY);
            INSERT INTO audit_runs VALUES ('audit-existing');
            CREATE TABLE scenarios (
              id VARCHAR(100), version VARCHAR(20), name VARCHAR(200), description TEXT,
              category VARCHAR(80), prerequisites JSON, configuration JSON, procedure JSON,
              success_criteria JSON, failure_criteria JSON, "references" JSON, active BOOLEAN,
              PRIMARY KEY (id, version)
            );
            INSERT INTO scenarios VALUES ('legacy.scenario','1.0.0','Legacy','Preserve me','prompt-injection','{}','{}','[]','{}','{}','[]',1);
            CREATE TABLE evidence (
              id VARCHAR(36) PRIMARY KEY, project_id VARCHAR(36), finding_id VARCHAR(36),
              evidence_type VARCHAR(40), title VARCHAR(300), content TEXT, sha256 VARCHAR(64),
              created_at DATETIME
            );
            INSERT INTO evidence VALUES ('evidence-existing','project-existing',NULL,'prompt_test','Legacy evidence','preserve me','0000000000000000000000000000000000000000000000000000000000000000','2026-01-01');
            """
        )
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
    command.upgrade(config, "head")
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT name FROM scenarios").fetchone() == ("Legacy",)
        assert connection.execute("SELECT content FROM evidence").fetchone() == ("preserve me",)
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == ("0002_audit_evidence",)
        assert "expected_marker" in {row[1] for row in connection.execute("PRAGMA table_info(scenarios)")}
        assert "audit_run_id" in {row[1] for row in connection.execute("PRAGMA table_info(evidence)")}
