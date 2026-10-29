from __future__ import annotations

from conftest import APIClient


def test_health_is_minimal_and_public(client: APIClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "token" not in response.text.lower()


def test_api_rejects_missing_token(client: APIClient) -> None:
    response = client.get("/api/v1/projects")
    assert response.status_code == 401


def test_cors_preflight_reaches_restricted_cors_middleware(client: APIClient) -> None:
    response = client.options(
        "/api/v1/dashboard",
        headers={
            "Origin": "http://127.0.0.1:1420",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:1420"


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
