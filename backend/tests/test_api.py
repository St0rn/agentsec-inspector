from __future__ import annotations

import pytest
from conftest import APIClient
from fastapi.testclient import TestClient

from agentsec.database import SessionLocal
from agentsec.main import app
from agentsec.models import AgentEvent, AuditRun, AuditStatus, Evidence, Target
from agentsec.models import TestExecution as ExecutionRecord
from agentsec.routers import projects as project_router
from agentsec.services.llm_client import LLMResult


def test_health_is_minimal_and_public(client: APIClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "token" not in response.text.lower()


def test_fastapi_lifespan_starts_with_database_migrations() -> None:
    with TestClient(app) as startup_client:
        response = startup_client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "agentsec-backend"


def test_api_rejects_missing_token(client: APIClient) -> None:
    response = client.get("/api/v1/projects")
    assert response.status_code == 401


@pytest.mark.parametrize(
    "origin",
    [
        "http://tauri.localhost",
        "tauri://localhost",
        "http://localhost:1420",
        "http://127.0.0.1:1420",
    ],
)
def test_cors_preflight_reaches_restricted_cors_middleware(client: APIClient, origin: str) -> None:
    response = client.options(
        "/api/v1/dashboard",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_cors_rejects_an_unlisted_origin(client: APIClient) -> None:
    response = client.options(
        "/api/v1/projects",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_health_exposes_windows_tauri_cors_header(client: APIClient) -> None:
    response = client.get("/health", headers={"Origin": "http://tauri.localhost"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://tauri.localhost"


def test_project_full_crud_roundtrip(client: APIClient, headers: dict[str, str]) -> None:
    created = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "client_name": "CRUD Client",
            "engagement_name": "Windows desktop verification",
            "description": "Created by the API regression test",
            "authorized_scope": "Loopback only",
            "start_date": None,
            "end_date": None,
        },
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    listed = client.get("/api/v1/projects", headers=headers)
    assert any(item["id"] == project_id for item in listed.json())

    payload = {
        "client_name": "CRUD Client",
        "engagement_name": "Updated verification",
        "description": "Updated by the API regression test",
        "authorized_scope": "Loopback and local test data",
        "start_date": None,
        "end_date": None,
    }
    updated = client.put(f"/api/v1/projects/{project_id}", headers=headers, json=payload)
    assert updated.status_code == 200
    assert updated.json()["engagement_name"] == "Updated verification"

    deleted = client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/projects/{project_id}", headers=headers).status_code == 404


def test_target_edit_and_real_connection_test_contract(
    client: APIClient,
    headers: dict[str, str],
    project: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created = client.post(
        "/api/v1/targets",
        headers=headers,
        json={
            "project_id": project["id"],
            "name": "Range",
            "target_type": "chatbot",
            "endpoint": "http://127.0.0.1:8789/target/api/chat/stream",
            "configuration": {"response_format": "ndjson"},
            "remote_authorized": False,
        },
    )
    assert created.status_code == 201
    target_id = created.json()["id"]
    payload = created.json()
    payload.update(
        {
            "name": "Range edited",
            "configuration": {"message_path": "message", "response_format": "ndjson"},
        }
    )
    payload = {
        key: payload[key]
        for key in (
            "project_id",
            "name",
            "target_type",
            "endpoint",
            "configuration",
            "remote_authorized",
        )
    }
    updated = client.put(f"/api/v1/targets/{target_id}", headers=headers, json=payload)
    assert updated.status_code == 200
    assert updated.json()["name"] == "Range edited"
    assert (
        client.post(
            f"/api/v1/targets/{target_id}/test",
            headers=headers,
            json={"confirm_active_request": False},
        ).status_code
        == 409
    )

    async def fixture(*_args: object, **_kwargs: object) -> LLMResult:
        return LLMResult(
            "CONNECTED",
            {"type": "done"},
            [{"name": "search"}],
            [{"type": "done", "response": "CONNECTED"}],
            {"protocol": "ndjson", "model": "fixture"},
            True,
        )

    monkeypatch.setattr(project_router, "send_chat", fixture)
    tested = client.post(
        f"/api/v1/targets/{target_id}/test", headers=headers, json={"confirm_active_request": True}
    )
    assert tested.status_code == 200
    assert tested.json()["protocol"] == "ndjson"
    assert tested.json()["completed"] is True


def test_audit_detail_exports_and_attack_chain_layout_persist(
    client: APIClient, headers: dict[str, str], project: dict[str, object]
) -> None:
    with SessionLocal() as db:
        target = Target(
            project_id=str(project["id"]),
            name="History target",
            target_type="agent_lab",
            endpoint="http://127.0.0.1:9999",
            configuration={},
        )
        db.add(target)
        db.flush()
        audit = AuditRun(
            project_id=str(project["id"]),
            target_id=target.id,
            audit_type="custom_payload",
            status=AuditStatus.completed,
            passive=False,
            configuration={"security_objective": "Protect marker"},
            summary={"test_status": "PASS"},
        )
        db.add(audit)
        db.flush()
        db.add(
            ExecutionRecord(
                audit_run_id=audit.id,
                scenario_id="custom.fixture",
                scenario_version="1.0.0",
                status="PASS",
                request_data={"messages": [{"role": "user", "content": "test"}]},
                response_data={"text": "safe"},
                analysis={"rules": []},
            )
        )
        db.add(
            Evidence(
                project_id=str(project["id"]),
                audit_run_id=audit.id,
                evidence_type="prompt_test",
                title="Fixture",
                content="observable",
                sha256="0" * 64,
            )
        )
        db.add(
            AgentEvent(
                project_id=str(project["id"]),
                audit_run_id=audit.id,
                event_type="llm_exchange",
                actor="AgentSec",
                target="History target",
                payload={"status": "PASS"},
            )
        )
        audit_id = audit.id
        db.commit()
    detail = client.get(f"/api/v1/audits/{audit_id}/detail", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["executions"][0]["response_data"]["text"] == "safe"
    assert detail.json()["evidence"][0]["content"] == "observable"
    assert (
        client.get(f"/api/v1/audits/{audit_id}/export?format=json", headers=headers).status_code
        == 200
    )
    pdf = client.get(f"/api/v1/audits/{audit_id}/export?format=pdf", headers=headers)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    layout = {"nodes": {"AgentSec": {"x": 120, "y": 240}, "History target": {"x": 500, "y": 240}}}
    saved = client.put(f"/api/v1/attack-chain-layout/{project['id']}", headers=headers, json=layout)
    assert saved.status_code == 200
    assert (
        client.get(f"/api/v1/attack-chain-layout/{project['id']}", headers=headers).json() == layout
    )


def test_project_crud_and_isolation(
    client: APIClient, headers: dict[str, str], project: dict[str, object]
) -> None:
    project_id = project["id"]
    fetched = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert fetched.status_code == 200
    payload = fetched.json()
    payload["description"] = "Updated"
    payload = {
        key: payload[key]
        for key in (
            "client_name",
            "engagement_name",
            "description",
            "authorized_scope",
            "start_date",
            "end_date",
        )
    }
    updated = client.put(f"/api/v1/projects/{project_id}", headers=headers, json=payload)
    assert updated.status_code == 200
    assert updated.json()["description"] == "Updated"

    target = client.post(
        "/api/v1/targets",
        headers=headers,
        json={
            "project_id": project_id,
            "name": "Lab MCP",
            "target_type": "mcp_http",
            "endpoint": "http://127.0.0.1:9999/mcp",
            "configuration": {},
            "remote_authorized": False,
        },
    )
    assert target.status_code == 201
    assert len(client.get(f"/api/v1/targets?project_id={project_id}", headers=headers).json()) == 1
    missing_project = client.post(
        "/api/v1/targets",
        headers=headers,
        json={
            "project_id": "00000000-0000-0000-0000-000000000000",
            "name": "Bad",
            "target_type": "mcp_http",
            "endpoint": "https://example.invalid/mcp",
            "configuration": {},
            "remote_authorized": False,
        },
    )
    assert missing_project.status_code == 404


def test_target_accepts_https_chatbot_url(
    client: APIClient, headers: dict[str, str], project: dict[str, object]
) -> None:
    response = client.post(
        "/api/v1/targets",
        headers=headers,
        json={
            "project_id": project["id"],
            "name": "Support chatbot",
            "target_type": "chatbot",
            "endpoint": "https://chatbot.example.test/api/conversation",
            "configuration": {
                "message_path": "input.message",
                "response_path": "answer.text",
                "api_key_env": "CHATBOT_API_KEY",
                "api_key_header": "X-API-Key",
                "api_key_prefix": "",
            },
            "remote_authorized": True,
        },
    )
    assert response.status_code == 201
    assert response.json()["endpoint"].startswith("https://")


def test_validation_rejects_invalid_dates(client: APIClient, headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "client_name": "A",
            "engagement_name": "B",
            "authorized_scope": "C",
            "start_date": "2026-02-02",
            "end_date": "2026-01-01",
        },
    )
    assert response.status_code == 422


def test_target_rejects_plaintext_credentials(
    client: APIClient, headers: dict[str, str], project: dict[str, object]
) -> None:
    response = client.post(
        "/api/v1/targets",
        headers=headers,
        json={
            "project_id": project["id"],
            "name": "Unsafe target",
            "target_type": "openai",
            "endpoint": "http://127.0.0.1:9999",
            "configuration": {"headers": {"Authorization": "Bearer plaintext"}},
            "remote_authorized": False,
        },
    )
    assert response.status_code == 422


def test_jailbreak_scenario_creates_a_distinct_audit_type(
    client: APIClient, headers: dict[str, str], project: dict[str, object]
) -> None:
    target = client.post(
        "/api/v1/targets",
        headers=headers,
        json={
            "project_id": project["id"],
            "name": "Controlled LLM",
            "target_type": "custom_http",
            "endpoint": "http://127.0.0.1:9999/chat",
            "configuration": {},
            "remote_authorized": False,
        },
    )
    assert target.status_code == 201
    response = client.post(
        "/api/v1/audits/prompt",
        headers=headers,
        json={
            "project_id": project["id"],
            "target_id": target.json()["id"],
            "scenario_id": "jb.authority-impersonation",
            "scenario_version": "1.0.0",
            "security_objective": "Do not disclose the fictional marker",
            "confirm_active_test": True,
        },
    )
    assert response.status_code == 202
    assert response.json()["audit_type"] == "jailbreak"


def test_black_box_preview_contains_only_the_connector_request(
    client: APIClient, headers: dict[str, str], project: dict[str, object]
) -> None:
    target = client.post(
        "/api/v1/targets",
        headers=headers,
        json={
            "project_id": project["id"],
            "name": "Preview target",
            "target_type": "openai",
            "endpoint": "http://127.0.0.1:9999",
            "configuration": {
                "model": "fixture-model",
                "api_key_env": "AGENTSEC_PREVIEW_SECRET",
            },
            "remote_authorized": False,
        },
    )
    assert target.status_code == 201
    objective = "LOCAL_ONLY_OBJECTIVE_31F4"
    rule_value = "LOCAL_ONLY_RULE_72B9"
    response = client.post(
        "/api/v1/audits/prompt/preview",
        headers=headers,
        json={
            "project_id": project["id"],
            "target_id": target.json()["id"],
            "scenario_id": "pi.direct",
            "security_objective": objective,
            "security_rules": [
                {
                    "id": "local-rule",
                    "rule_type": "response_not_contains",
                    "value": rule_value,
                }
            ],
        },
    )
    assert response.status_code == 200
    preview = response.json()
    assert preview["test_mode"] == "black_box"
    assert [message["role"] for message in preview["messages"]] == ["user"]
    assert preview["payload"]["messages"] == preview["messages"]
    assert preview["security_objective_sent"] is False
    assert preview["evaluation_rules_sent"] is False
    assert objective not in response.text
    assert rule_value not in response.text
    assert "AGENTSEC_PREVIEW_SECRET" not in response.text
    assert "secret values are never previewed" in preview["authentication"]


def test_controlled_lab_preview_requires_confirmation_and_adds_system_message(
    client: APIClient, headers: dict[str, str], project: dict[str, object]
) -> None:
    target = client.post(
        "/api/v1/targets",
        headers=headers,
        json={
            "project_id": project["id"],
            "name": "Controlled target",
            "target_type": "ollama",
            "endpoint": "http://127.0.0.1:11434",
            "configuration": {"model": "fixture-model"},
            "remote_authorized": False,
        },
    )
    body = {
        "project_id": project["id"],
        "target_id": target.json()["id"],
        "scenario_id": "pi.direct",
        "security_objective": "Test the controlled boundary",
        "test_mode": "controlled_lab",
        "marker_provenance": "controlled_lab",
        "system_instruction": "Protect the controlled marker.",
    }
    rejected = client.post("/api/v1/audits/prompt/preview", headers=headers, json=body)
    assert rejected.status_code == 422
    accepted = client.post(
        "/api/v1/audits/prompt/preview",
        headers=headers,
        json={**body, "confirm_controlled_lab": True},
    )
    assert accepted.status_code == 200
    preview = accepted.json()
    assert [message["role"] for message in preview["messages"]] == ["system", "user"]
    assert "AGENTSEC_CANARY_7F3A" in preview["messages"][0]["content"]
    assert "AGENTSEC_CANARY_7F3A" not in preview["messages"][1]["content"]
    assert preview["payload"]["messages"] == preview["messages"]
    assert preview["url"].endswith("/api/chat")


def test_finding_history(
    client: APIClient, headers: dict[str, str], project: dict[str, object]
) -> None:
    response = client.post(
        "/api/v1/findings",
        headers=headers,
        json={
            "project_id": project["id"],
            "title": "Manual observation",
            "description": "Evidence-based note",
            "component": "lab",
            "classification": "Observation",
            "severity": "low",
            "confidence": "high",
        },
    )
    assert response.status_code == 201
    finding = response.json()
    changed = client.put(
        f"/api/v1/findings/{finding['id']}", headers=headers, json={"status": "Confirmed"}
    )
    assert changed.status_code == 200
    history = client.get(f"/api/v1/findings/{finding['id']}/history", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 2


def test_dashboard_contains_only_persisted_counts(
    client: APIClient, headers: dict[str, str], project: dict[str, object]
) -> None:
    response = client.get("/api/v1/dashboard", headers=headers)
    assert response.status_code == 200
    assert response.json()["projects"] >= 1
