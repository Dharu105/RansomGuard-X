"""Defense memory and prediction-vs-reality learning."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.learning.models import EMPTY_SUMMARY, EVENT_TO_ACTION, EVENT_TO_TARGET
from app.models import DefenseMemory, Prediction

# Survives simulation reset. Cleared only if the process restarts.
_PRED_SEQ = 0
_RESOLVED: list[dict[str, Any]] = []
_ADJUSTMENTS: dict[str, float] = {}
_DEFENSE_MEM: dict[str, dict[str, Any]] = {}
ADJ_MIN, ADJ_MAX = -10.0, 10.0


def _next_id() -> str:
    global _PRED_SEQ
    _PRED_SEQ += 1
    return f"PRED-{_PRED_SEQ:04d}"


def adjustments() -> dict[str, float]:
    return dict(_ADJUSTMENTS)


def defense_memory_list() -> list[dict[str, Any]]:
    return list(_DEFENSE_MEM.values())


def new_prediction(forecast: dict[str, Any], event: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "prediction_id": _next_id(),
        "timestamp": (event or {}).get("timestamp") or datetime.utcnow().isoformat(),
        "current_node": forecast.get("current_node"),
        "current_stage": forecast.get("current_stage"),
        "predicted_target": forecast.get("predicted_target"),
        "predicted_action": forecast.get("predicted_action"),
        "confidence": forecast.get("confidence") or 0,
        "actual_target": None,
        "actual_action": None,
        "outcome": "UNRESOLVED",
        "target_correct": None,
        "action_correct": None,
        "prediction_error": None,
        "simulated": True,
        "label": "SIMULATION / EXPERIMENTAL",
    }


def resolve(pending: dict[str, Any], actual_event: dict[str, Any]) -> dict[str, Any]:
    ev_type = actual_event.get("event_type")
    actual_target = EVENT_TO_TARGET.get(ev_type)
    actual_action = EVENT_TO_ACTION.get(ev_type)
    target_correct = bool(pending.get("predicted_target") and pending["predicted_target"] == actual_target)
    action_correct = bool(pending.get("predicted_action") and pending["predicted_action"] == actual_action)
    if target_correct and action_correct:
        outcome = "CORRECT"
        error = 0.0
    elif target_correct or action_correct:
        outcome = "PARTIAL"
        error = 0.5
    else:
        outcome = "INCORRECT"
        error = 1.0
    row = dict(pending)
    row.update(
        {
            "actual_target": actual_target,
            "actual_action": actual_action,
            "actual_event": ev_type,
            "outcome": outcome,
            "target_correct": target_correct,
            "action_correct": action_correct,
            "prediction_error": error,
            "resolved_at": datetime.utcnow().isoformat(),
        }
    )
    _RESOLVED.append(row)
    _apply_adjustment(row)
    return row


def _apply_adjustment(row: dict[str, Any]) -> None:
    predicted = row.get("predicted_target")
    actual = row.get("actual_target")
    if not predicted or not actual:
        return
    if predicted == actual:
        _ADJUSTMENTS[actual] = max(ADJ_MIN, min(ADJ_MAX, _ADJUSTMENTS.get(actual, 0.0) + 1.0))
        return
    _ADJUSTMENTS[predicted] = max(ADJ_MIN, min(ADJ_MAX, _ADJUSTMENTS.get(predicted, 0.0) - 2.0))
    _ADJUSTMENTS[actual] = max(ADJ_MIN, min(ADJ_MAX, _ADJUSTMENTS.get(actual, 0.0) + 2.0))


def record_defense_outcome(action: str | None, adaptation: dict[str, Any] | None) -> None:
    if not action or not adaptation:
        return
    scenarios = adaptation.get("scenarios") or []
    _DEFENSE_MEM[action] = {
        "defense_action": action,
        "previous_outcome": (scenarios[0].get("outcome") if scenarios else None),
        "adaptive_outcome": (scenarios[-1].get("outcome") if scenarios else None),
        "robustness": adaptation.get("robustness_class"),
        "robustness_score": adaptation.get("robustness_score"),
        "updated_at": datetime.utcnow().isoformat(),
        "simulated": True,
        "label": "SIMULATION / EXPERIMENTAL",
    }


def summarize(current_unresolved: dict[str, Any] | None = None, current_resolved: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    resolved = list(_RESOLVED)
    correct = sum(1 for r in resolved if r.get("outcome") == "CORRECT")
    partial = sum(1 for r in resolved if r.get("outcome") == "PARTIAL")
    incorrect = sum(1 for r in resolved if r.get("outcome") == "INCORRECT")
    n = len(resolved)
    t_ok = sum(1 for r in resolved if r.get("target_correct"))
    a_ok = sum(1 for r in resolved if r.get("action_correct"))
    overall = round(100.0 * (correct + 0.5 * partial) / n, 1) if n else 0.0
    target_acc = round(100.0 * t_ok / n, 1) if n else 0.0
    action_acc = round(100.0 * a_ok / n, 1) if n else 0.0
    total = n + (1 if current_unresolved and current_unresolved.get("outcome") == "UNRESOLVED" else 0)
    adjustments = [
        {"target": k, "historical_adjustment": v, "note": "Bounded -10..+10. Current evidence remains primary."}
        for k, v in sorted(_ADJUSTMENTS.items())
    ]
    return {
        "total_predictions": total if total else n,
        "resolved_predictions": n,
        "correct_predictions": correct,
        "partial_predictions": partial,
        "incorrect_predictions": incorrect,
        "target_accuracy": target_acc,
        "action_accuracy": action_acc,
        "overall_accuracy": overall,
        "recent_outcomes": list(reversed(resolved[-12:])),
        "memory_adjustments": adjustments,
        "defense_memory": defense_memory_list(),
        "current_unresolved": current_unresolved,
        "label": "SIMULATION / EXPERIMENTAL",
        "disclaimer": "Based on synthetic simulation history. Not production-world accuracy.",
        "simulated": True,
    }


def snapshot_learning(state: dict[str, Any]) -> dict[str, Any]:
    openp = state.get("open_prediction")
    current = list(state.get("prediction_outcomes") or [])
    summary = summarize(openp, current)
    return {
        "summary": summary,
        "recent_outcomes": summary["recent_outcomes"],
        "memory_adjustments": summary["memory_adjustments"],
        "defense_memory": summary["defense_memory"],
        "open_prediction": openp,
        "label": "SIMULATION / EXPERIMENTAL",
        "simulated": True,
    }


def record_memory(
    db: Session,
    incident_id: str,
    pattern: str,
    defense_used: str,
    outcome: str,
    impact: dict[str, Any],
    decision_quality: str,
    recommended_future: str,
) -> dict[str, Any]:
    row = DefenseMemory(
        incident_id=incident_id,
        pattern=pattern,
        defense_used=defense_used,
        outcome=outcome,
        impact=json.dumps(impact),
        decision_quality=decision_quality,
        recommended_future=recommended_future,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize_row(row)


def serialize_row(row: DefenseMemory) -> dict[str, Any]:
    return {
        "id": row.id,
        "incident_id": row.incident_id,
        "pattern": row.pattern,
        "defense_used": row.defense_used,
        "outcome": row.outcome,
        "impact": json.loads(row.impact or "{}"),
        "decision_quality": row.decision_quality,
        "recommended_future": row.recommended_future,
        "created_at": row.created_at.isoformat() if row.created_at else "",
    }


def list_memory(db: Session) -> list[dict[str, Any]]:
    rows = db.query(DefenseMemory).order_by(DefenseMemory.id.desc()).all()
    return [serialize_row(r) for r in rows]


def compare_prediction(predicted: str, actual: str, confidence: float) -> dict[str, Any]:
    correct = predicted == actual
    return {
        "predicted_target": predicted,
        "actual_target": actual,
        "prediction_confidence": confidence,
        "correct": correct,
        "predicted_propagation": ["LAB-PC-21", "FAC-PC-07", predicted] if predicted else [],
        "actual_propagation": ["LAB-PC-21", "FAC-PC-07", actual] if actual else [],
        "simulated": True,
    }


def quality_from_regret(regret: float) -> str:
    if regret < 12:
        return "excellent"
    if regret < 28:
        return "good"
    if regret < 50:
        return "fair"
    return "poor"
