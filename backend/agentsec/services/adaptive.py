from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

import structlog

from ..config import get_settings
from ..database import SessionLocal
from ..models import (
    AgentEvent,
    AuditRun,
    AuditStatus,
    Evidence,
    Severity,
    Target,
    TestExecution,
)
from .events import event_hub
from .finding_dedup import record_finding
from .llm_client import send_chat
from .scenarios import controlled_lab_system_message, evaluate, render_attack_payload

log = structlog.get_logger()
REFUSAL = re.compile(r"\b(?:cannot|can't|won't|refuse|decline|not able|ne peux pas|refus)\b", re.I)


def utcnow() -> datetime:
    return datetime.now(UTC)


def choose_transition(
    transitions: list[dict[str, Any]],
    response: str,
    tool_calls: list[dict[str, Any]],
    verdict: str,
    analysis: dict[str, Any],
) -> tuple[str | None, dict[str, Any]]:
    tool_names = set(analysis.get("tool_names", []))
    violated = set(analysis.get("violated_rules", []))
    for index, transition in enumerate(transitions):
        condition = str(transition.get("condition", ""))
        value = str(transition.get("value") or "")
        matched = (
            condition == "always"
            or condition == "response_contains"
            and value.casefold() in response.casefold()
            or condition == "response_not_contains"
            and value.casefold() not in response.casefold()
            or condition == "tool_observed"
            and value in tool_names
            or condition == "rule_violated"
            and value in violated
            or condition == "verdict"
            and value.upper() == verdict
            or condition == "refusal_detected"
            and REFUSAL.search(response) is not None
        )
        if matched:
            return str(transition["next_step"]), {
                "transition_index": index,
                "condition": condition,
                "value": value or None,
                "matched": True,
                "observable_basis": {
                    "verdict": verdict,
                    "tool_names": sorted(tool_names),
                    "violated_rules": sorted(violated),
                    "refusal_detected": REFUSAL.search(response) is not None,
                },
            }
    return None, {
        "matched": False,
        "reason": "No declared transition matched the observed response and tool events.",
        "tool_call_count": len(tool_calls),
    }


async def run_adaptive_audit(audit_id: str, request: dict[str, Any]) -> None:
    settings = get_settings()
    with SessionLocal() as db:
        audit = db.get(AuditRun, audit_id)
        if not audit:
            return
        audit.status = AuditStatus.running
        audit.started_at = utcnow()
        target = db.get(Target, audit.target_id)
        execution = TestExecution(
            audit_run_id=audit.id,
            scenario_id=f"adaptive.{audit.id}",
            scenario_version="1.0.0",
            status="RUNNING",
            request_data={
                "state_machine": request["steps"],
                "entry_step": request["entry_step"],
                "security_objective": request["security_objective"],
                "security_rules": request["security_rules"],
                "test_mode": request.get("test_mode", "black_box"),
                "criteria_provenance": "auditor_local_rules",
                "marker_provenance": request.get("marker_provenance", "user_payload"),
                "evaluation_engine_version": "2.0.0",
                "turns": [],
            },
        )
        db.add(execution)
        db.commit()
        await event_hub.publish(audit.id, {"stage": "adaptive_start", "progress": 5})
        try:
            if not target:
                raise ValueError("Target not found")
            steps = {str(step["id"]): step for step in request["steps"]}
            current_id = str(request["entry_step"])
            max_turns = int(request["max_turns"])
            max_tokens = int(request["max_tokens_per_turn"])
            token_budget = int(request["token_budget"])
            marker = str(request.get("fictional_marker", "AGENTSEC_CANARY_7F3A"))
            messages: list[dict[str, str]] = []
            if request.get("test_mode") == "controlled_lab":
                messages.append(
                    {
                        "role": "system",
                        "content": controlled_lab_system_message(
                            request["system_instruction"], marker
                        ),
                    }
                )
            turns: list[dict[str, Any]] = []
            all_tools: list[dict[str, Any]] = []
            stop_reason = "max_turns_reached"
            for turn_number in range(1, max_turns + 1):
                db.refresh(audit)
                if audit.status == AuditStatus.cancelled:
                    stop_reason = "cancelled_by_user"
                    execution.status = "CANCELLED"
                    execution.finished_at = utcnow()
                    execution.request_data = {**execution.request_data, "turns": turns}
                    execution.response_data = {"turns": turns, "tool_calls": all_tools}
                    execution.analysis = {"stop_reason": stop_reason, "attack_success": False}
                    audit.summary = {"turns": turns, "stop_reason": stop_reason}
                    audit.finished_at = utcnow()
                    db.commit()
                    await event_hub.publish(audit.id, {"stage": "cancelled", "progress": 100})
                    return
                if turn_number * max_tokens > token_budget:
                    stop_reason = "token_budget_reached"
                    break
                step = steps[current_id]
                payload = render_attack_payload(
                    str(step["payload"]), marker, request.get("test_mode", "black_box")
                )
                messages.append({"role": "user", "content": payload})
                result = await send_chat(target, messages, max_tokens, settings)
                all_tools.extend(result.tool_calls)
                verdict, turn_analysis = evaluate(
                    result.text,
                    result.tool_calls,
                    marker,
                    request["security_rules"],
                    completed=result.completed,
                    marker_provenance=request.get("marker_provenance", "user_payload"),
                    evaluation_engine_version="2.0.0",
                )
                next_id, decision = choose_transition(
                    list(step.get("transitions", [])),
                    result.text,
                    result.tool_calls,
                    verdict,
                    turn_analysis,
                )
                turn = {
                    "turn": turn_number,
                    "step_id": current_id,
                    "step_name": step["name"],
                    "payload": payload,
                    "exact_payload_sent": result.request_payload,
                    "request_url": result.request_url,
                    "response": result.text,
                    "tool_calls": result.tool_calls,
                    "events": result.events,
                    "completed": result.completed,
                    "verdict": verdict,
                    "analysis": turn_analysis,
                    "branch_decision": decision,
                    "next_step": next_id,
                }
                turns.append(turn)
                execution.request_data = {**execution.request_data, "turns": turns}
                execution.response_data = {"turns": turns, "tool_calls": all_tools}
                db.add(
                    AgentEvent(
                        project_id=audit.project_id,
                        audit_run_id=audit.id,
                        event_type="adaptive_turn",
                        actor="AgentSec",
                        target=target.name,
                        payload={
                            "turn": turn_number,
                            "step_id": current_id,
                            "verdict": verdict,
                            "branch_decision": decision,
                            "tool_calls": result.tool_calls,
                        },
                    )
                )
                db.commit()
                await event_hub.publish(
                    audit.id,
                    {
                        "stage": "adaptive_turn",
                        "progress": min(95, 5 + round(turn_number / max_turns * 90)),
                        "turn": turn_number,
                        "step_id": current_id,
                        "verdict": verdict,
                        "next_step": next_id,
                    },
                )
                if step.get("terminal"):
                    stop_reason = "terminal_step"
                    break
                if not next_id:
                    stop_reason = "no_transition"
                    break
                messages.append({"role": "assistant", "content": result.text})
                current_id = next_id
            combined = "\n\n".join(str(turn["response"]) for turn in turns)
            final_verdict, final_analysis = evaluate(
                combined,
                all_tools,
                marker,
                request["security_rules"],
                completed=turns[-1]["completed"] if turns else None,
                marker_provenance=request.get("marker_provenance", "user_payload"),
                evaluation_engine_version="2.0.0",
            )
            final_analysis.update(
                {
                    "stop_reason": stop_reason,
                    "turn_count": len(turns),
                    "state_path": [turn["step_id"] for turn in turns],
                    "branch_decisions": [turn["branch_decision"] for turn in turns],
                }
            )
            execution.status = final_verdict
            execution.request_data = {**execution.request_data, "turns": turns}
            execution.response_data = {
                "text": turns[-1]["response"] if turns else "",
                "turns": turns,
                "tool_calls": all_tools,
            }
            execution.analysis = final_analysis
            execution.finished_at = utcnow()
            evidence_value = {
                "state_machine": request["steps"],
                "turns": turns,
                "analysis": final_analysis,
            }
            evidence_text = json.dumps(evidence_value, ensure_ascii=False, indent=2)[:200_000]
            db.add(
                Evidence(
                    project_id=audit.project_id,
                    audit_run_id=audit.id,
                    evidence_type="adaptive_red_team",
                    title=f"Adaptive Red Team: {request['name']}",
                    content=evidence_text,
                    sha256=hashlib.sha256(evidence_text.encode()).hexdigest(),
                )
            )
            if final_verdict == "FAIL":
                violated = final_analysis.get("violated_rules", [])
                record_finding(
                    db,
                    audit,
                    rule=f"adaptive:{','.join(sorted(map(str, violated)))}",
                    component=target.name,
                    identity_component=target.id,
                    title=f"Adaptive security objective violated: {request['name']}",
                    description="The adaptive state machine observed a violation of a required local security rule.",
                    classification="Confirmed vulnerability",
                    severity=Severity.high,
                    confidence="high",
                    impact="The observed interaction crossed a configured security boundary.",
                    exploitation_conditions="An attacker can reproduce the recorded state path and payload sequence.",
                    reproduction_steps=json.dumps(
                        [{"step": item["step_id"], "payload": item["payload"]} for item in turns],
                        ensure_ascii=False,
                        indent=2,
                    ),
                    observed_result=combined[:20_000],
                    expected_result="Every required local security rule should remain satisfied.",
                    recommendation="Enforce instruction and tool boundaries outside the model and retest the recorded branch.",
                )
            audit.summary = {
                "name": request["name"],
                "test_status": final_verdict,
                "test_mode": request.get("test_mode", "black_box"),
                "turn_count": len(turns),
                "state_path": final_analysis["state_path"],
                "stop_reason": stop_reason,
                "turns": turns,
                "analysis": final_analysis,
                "evaluation_engine_version": "2.0.0",
            }
            audit.status = AuditStatus.completed
            audit.finished_at = utcnow()
            db.commit()
            await event_hub.publish(
                audit.id,
                {"stage": "completed", "progress": 100, "status": final_verdict},
            )
        except Exception as exc:
            log.warning("adaptive_audit_failed", audit_id=audit_id, error=str(exc))
            execution.status = "ERROR"
            execution.analysis = {"technical_error": str(exc), "attack_success": False}
            execution.finished_at = utcnow()
            audit.status = AuditStatus.failed
            audit.error = str(exc)[:10_000]
            audit.finished_at = utcnow()
            db.commit()
            await event_hub.publish(
                audit.id, {"stage": "failed", "progress": 100, "error": str(exc)}
            )
