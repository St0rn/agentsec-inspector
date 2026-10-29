from __future__ import annotations

import pytest

from agentsec.config import Settings
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
