from __future__ import annotations

import pytest

from agentsec.config import Settings
from agentsec.schemas import TargetCreate
from agentsec.security import (
    SecretStore,
    TargetSecurityError,
    safe_evidence_path,
    validate_outbound_url,
)
from agentsec.services.mcp_analysis import analyse_discovery
from agentsec.services.scenarios import SCENARIOS, evaluate, scenario_messages


def test_ssrf_rejects_metadata_and_remote_without_authorisation(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path)
    with pytest.raises(TargetSecurityError):
        validate_outbound_url(
            "http://169.254.169.254/latest/meta-data", remote_authorized=True, settings=settings
        )
    with pytest.raises(TargetSecurityError):
        validate_outbound_url("https://example.com", remote_authorized=False, settings=settings)
    assert validate_outbound_url(
        "http://127.0.0.1:8000", remote_authorized=False, settings=settings
    )


def test_safe_path_and_secret_roundtrip(tmp_path) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    assert safe_evidence_path(root, "item.json").parent == root
    with pytest.raises(TargetSecurityError):
        safe_evidence_path(root, "../escape")
    store = SecretStore(tmp_path)
    encrypted = store.encrypt("fictional-secret")
    assert "fictional-secret" not in encrypted
    assert store.decrypt(encrypted) == "fictional-secret"


def test_mcp_analysis_is_conservative() -> None:
    issues = analyse_discovery(
        {
            "tools": [
                {
                    "name": "delete_file",
                    "description": "Delete a file",
                    "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}},
                }
            ]
        }
    )
    assert issues
    assert all(issue["classification"] != "Confirmed vulnerability" for issue in issues)


def test_prompt_classification_never_maps_empty_to_success() -> None:
    assert evaluate("AGENTSEC_CANARY_7F3A", [], "AGENTSEC_CANARY_7F3A")[0] == "FAIL"
    assert evaluate("", [], "AGENTSEC_CANARY_7F3A")[0] == "INCONCLUSIVE"
    assert evaluate("I cannot comply.", [], "AGENTSEC_CANARY_7F3A")[0] == "PASS"


def test_multi_turn_scenario_contains_prior_exchange() -> None:
    scenario = next(item for item in SCENARIOS if item["id"] == "pi.multi-turn")
    messages = scenario_messages(scenario, "AGENTSEC_CANARY_7F3A", "Protect it")
    assert [item["role"] for item in messages] == ["system", "user", "assistant", "user"]


def test_jailbreak_catalog_is_versioned_and_uses_only_fictional_markers() -> None:
    scenarios = [item for item in SCENARIOS if item["category"] == "jailbreak"]
    assert len(scenarios) == 9
    assert len({item["id"] for item in scenarios}) == len(scenarios)
    for scenario in scenarios:
        assert scenario["id"].startswith("jb.")
        assert scenario["version"] == "1.0.0"
        assert "{marker}" in scenario["template"]
        assert scenario["references"]
        messages = scenario_messages(scenario, "AGENTSEC_CANARY_7F3A", "Protect it")
        assert messages[-1]["role"] == "user"
        assert "AGENTSEC_CANARY_7F3A" in messages[-1]["content"]


def test_target_url_validation_accepts_web_urls_and_rejects_unsafe_forms() -> None:
    common = {"project_id": "project", "name": "Chatbot", "target_type": "chatbot"}
    assert TargetCreate(**common, endpoint="http://127.0.0.1:8000/chat").endpoint
    assert TargetCreate(**common, endpoint="https://chatbot.example.test/chat").endpoint
    with pytest.raises(ValueError, match="http:// or https://"):
        TargetCreate(**common, endpoint="ftp://chatbot.example.test/chat")
    with pytest.raises(ValueError, match="requires"):
        TargetCreate(**common, endpoint=None)
    with pytest.raises(ValueError, match="Credentials"):
        TargetCreate(**common, endpoint="https://user:password@example.test/chat")


def test_target_configuration_rejects_plaintext_api_key_headers() -> None:
    with pytest.raises(ValueError, match="Plaintext credentials"):
        TargetCreate(
            project_id="project",
            name="Unsafe chatbot",
            target_type="chatbot",
            endpoint="https://example.test/chat",
            configuration={"headers": {"X-API-Key": "plaintext-secret"}},
        )
