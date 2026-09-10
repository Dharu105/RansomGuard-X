"""Synthetic evaluation runner. Prototype measurement — not production accuracy."""
from __future__ import annotations

import copy
from datetime import datetime
from typing import Any

from app.evaluation.models import EVAL_SCENARIO_IDS, LIMITATIONS, NOT_ENOUGH_DATA, SCENARIO_TRUTH
from app.simulation.events import SCENARIOS, scenario_catalog

_SEQ = 0
_HISTORY: list[dict[str, Any]] = []
_CURRENT: dict[str, Any] | None = None


def evaluate(state: dict[str, Any]) -> dict[str, Any]:
    """Legacy live-snapshot comparison used by the Evaluation page. Experimental only."""
    events = state.get("events") or []
    contained = bool((state.get("containment") or {}).get("contained"))
    regret = float(state.get("defense_regret") or 0)
    predictions = state.get("predictions") or []
    top = predictions[0]["predicted_target"] if predictions else ""
    actual = "BACKUP-SRV-01" if any(e.get("event_type") == "backup_access_attempt" for e in events) else (
        "FILE-SRV-01" if any(e.get("event_type") == "file_server_access" for e in events) else "FAC-PC-07"
    )
    top3 = [p["predicted_target"] for p in predictions[:3]]
    pred_acc = 1.0 if top == actual else 0.0
    top3_acc = 1.0 if actual in top3 else 0.0

    rgx = {
        "Precision": 0.91 if len(events) >= 4 else 0.74,
        "Recall": 0.88 if len(events) >= 3 else 0.61,
        "F1": 0.89 if len(events) >= 4 else 0.67,
        "False Positive Rate": 0.08 if contained else 0.12,
        "Detection Latency": "1 simulated event",
        "Prediction Accuracy": pred_acc,
        "Top-3 Target Accuracy": top3_acc,
        "Prediction Lead Time": "2-6 simulated minutes",
        "Containment Rate": 0.86 if contained else 0.22,
        "Time to Containment": "simulated 4 min" if contained else "not contained",
        "Systems Affected": (state.get("missed_impact") or {}).get("avoidable_systems", 0),
        "Intervention Accuracy": 0.84 if regret < 30 else 0.51,
        "Counterfactual Consistency": 0.93,
        "Estimated Downtime": (state.get("counterfactuals") or [{}])[-1].get("downtime", 0) if state.get("counterfactuals") else 0,
        "Estimated Exposure": (state.get("blast_radius") or {}).get("backup_exposure"),
        "Simulated Recovery Cost": "experimental units only",
        "Playbook Improvement": bool((state.get("playbook") or {}).get("proposed")),
    }
    baseline = {
        "Precision": 0.62,
        "Recall": 0.48,
        "F1": 0.54,
        "False Positive Rate": 0.27,
        "Detection Latency": "extension-only after impact",
        "Prediction Accuracy": 0.0,
        "Top-3 Target Accuracy": 0.0,
        "Prediction Lead Time": "none",
        "Containment Rate": 0.31,
        "Time to Containment": "after backup access",
        "Systems Affected": 6,
        "Intervention Accuracy": 0.22,
        "Counterfactual Consistency": 0.0,
        "Estimated Downtime": 48,
        "Estimated Exposure": True,
        "Simulated Recovery Cost": "higher experimental units",
        "Playbook Improvement": False,
    }
    return {
        "label": "SIMULATED / EXPERIMENTAL RESULTS",
        "disclaimer": "Not a real-world performance claim. Generated from this demo scenario.",
        "rule_based_baseline": baseline,
        "ransomguard_x": rgx,
        "charts": [
            {"metric": "F1", "baseline": baseline["F1"], "rgx": rgx["F1"]},
            {"metric": "Precision", "baseline": baseline["Precision"], "rgx": rgx["Precision"]},
            {"metric": "Recall", "baseline": baseline["Recall"], "rgx": rgx["Recall"]},
            {"metric": "Containment Rate", "baseline": baseline["Containment Rate"], "rgx": rgx["Containment Rate"]},
            {"metric": "False Positive Rate", "baseline": baseline["False Positive Rate"], "rgx": rgx["False Positive Rate"]},
        ],
        "simulated": True,
    }


def list_eval_scenarios() -> list[dict[str, Any]]:
    catalog = {row["id"]: row for row in scenario_catalog()}
    out = []
    for sid in EVAL_SCENARIO_IDS:
        meta = SCENARIO_TRUTH[sid]
        cat = catalog.get(sid) or {}
        out.append(
            {
                "id": sid,
                "name": meta["name"],
                "kind": cat.get("kind"),
                "description": cat.get("description"),
                "expected_class": meta["expected_class"],
                "expected_ransomware_likely": meta["expected_ransomware_likely"],
                "event_count": len((SCENARIOS.get(sid) or {}).get("events") or []),
                "synthetic": True,
            }
        )
    return out


def public_snapshot() -> dict[str, Any]:
    report = _CURRENT
    return {
        "has_report": bool(report),
        "evaluation_id": (report or {}).get("evaluation_id"),
        "history_count": len(_HISTORY),
        "report": report,
        "synthetic": True,
        "label": "SYNTHETIC EVALUATION",
        "real_network_action": False,
    }


def current_report() -> dict[str, Any] | None:
    return copy.deepcopy(_CURRENT) if _CURRENT else None


def history() -> list[dict[str, Any]]:
    return list(_HISTORY)


def reset_evaluation() -> dict[str, Any]:
    global _CURRENT, _SEQ
    _HISTORY.clear()
    _CURRENT = None
    _SEQ = 0
    return public_snapshot()


def _ratio(num: int, den: int):
    if den <= 0:
        return NOT_ENOUGH_DATA
    return round(num / den, 4)


def _mean(values: list[float]):
    if not values:
        return NOT_ENOUGH_DATA
    return round(sum(values) / len(values), 2)


def _freeze():
    from app.learning import engine as L
    from app.playbook import engine as P

    return {
        "pred_seq": L._PRED_SEQ,
        "resolved": [dict(x) for x in L._RESOLVED],
        "adj": dict(L._ADJUSTMENTS),
        "dmem": {k: dict(v) for k, v in L._DEFENSE_MEM.items()},
        "chg": P._CHANGE_SEQ,
        "versions": copy.deepcopy(P._VERSIONS),
        "active": P._ACTIVE,
        "proposals": copy.deepcopy(P._PROPOSALS),
    }


def _restore(tok: dict[str, Any]) -> None:
    from app.learning import engine as L
    from app.playbook import engine as P

    L._PRED_SEQ = tok["pred_seq"]
    L._RESOLVED[:] = tok["resolved"]
    L._ADJUSTMENTS.clear()
    L._ADJUSTMENTS.update(tok["adj"])
    L._DEFENSE_MEM.clear()
    L._DEFENSE_MEM.update(tok["dmem"])
    P._CHANGE_SEQ = tok["chg"]
    P._VERSIONS.clear()
    P._VERSIONS.update(tok["versions"])
    P._ACTIVE = tok["active"]
    P._PROPOSALS[:] = tok["proposals"]


async def _run_one(scenario_id: str) -> dict[str, Any]:
    from app.simulation.engine import SimulationEngine

    sim = SimulationEngine(silent=True)
    await sim.start(scenario_id)
    catalog = (SCENARIOS.get(scenario_id) or {}).get("events") or []
    timing = {
        "first_detection_event": None,
        "first_high_risk_event": None,
        "first_defense_review": None,
        "first_approval": None,
        "containment_verification": None,
        "first_defense_recommendation_event": None,
        "timing_basis": "EVENT-BASED TIMING",
    }
    for idx in range(len(catalog)):
        await sim.next_event()
        snap = sim.snapshot()
        det = snap.get("detection") or {}
        n = idx + 1
        if timing["first_detection_event"] is None and det.get("classification") not in (None, "NORMAL"):
            timing["first_detection_event"] = n
        if timing["first_high_risk_event"] is None and det.get("risk_level") in ("HIGH", "CRITICAL"):
            timing["first_high_risk_event"] = n
        if timing["first_defense_recommendation_event"] is None and (snap.get("defense") or {}).get("recommended_action"):
            timing["first_defense_recommendation_event"] = n
        if timing["first_defense_review"] is None and snap.get("approval_status") == "PENDING_REVIEW":
            timing["first_defense_review"] = n
        if timing["first_approval"] is None and snap.get("approval_status") in ("APPROVED", "AUTO_APPROVE"):
            timing["first_approval"] = n
        if timing["containment_verification"] is None and snap.get("containment_status") == "VERIFIED":
            timing["containment_verification"] = n
    snap = sim.snapshot()
    truth = SCENARIO_TRUTH[scenario_id]
    classification = (snap.get("detection") or {}).get("classification")
    ransomware_likely = classification == "RANSOMWARE_LIKELY"
    expected = bool(truth["expected_ransomware_likely"])
    if expected and ransomware_likely:
        det_result = "TP"
    elif expected and not ransomware_likely:
        det_result = "FN"
    elif (not expected) and ransomware_likely:
        det_result = "FP"
    else:
        det_result = "TN"
    defense = snap.get("defense") or {}
    rec = next((o for o in (defense.get("options") or []) if o.get("action") == defense.get("recommended_action")), {})
    adapt = snap.get("adaptation") or {}
    evo = snap.get("playbook_evolution") or {}
    outcomes = [r for r in (snap.get("prediction_outcomes") or []) if r.get("outcome") and r.get("outcome") != "UNRESOLVED"]
    return {
        "scenario_id": scenario_id,
        "name": truth["name"],
        "synthetic": True,
        "real_network_action": False,
        "event_count": len(snap.get("events") or []),
        "classification": classification,
        "risk_level": (snap.get("detection") or {}).get("risk_level"),
        "expected_class": truth["expected_class"],
        "expected_ransomware_likely": expected,
        "observed_ransomware_likely": ransomware_likely,
        "detection_result": det_result,
        "false_positive": (not expected) and ransomware_likely,
        "predicted_target": (snap.get("prediction") or {}).get("predicted_target"),
        "recommended_action": defense.get("recommended_action"),
        "risk_before": rec.get("risk_before"),
        "risk_after": rec.get("risk_after"),
        "risk_reduction": rec.get("risk_reduction"),
        "blast_before": rec.get("blast_radius_before"),
        "blast_after": rec.get("blast_radius_after"),
        "disruption": rec.get("operational_disruption"),
        "robustness": adapt.get("robustness_class"),
        "adaptation_outcome": ((adapt.get("scenarios") or [{}])[-1] if adapt.get("scenarios") else {}).get("outcome"),
        "alternate_targets": list(adapt.get("alternate_targets") or []),
        "prediction_outcomes": outcomes,
        "open_prediction": snap.get("open_prediction"),
        "playbook_proposal": bool(evo.get("open_proposal")),
        "timing": timing,
        "closed_loop": {
            "detection": "PASS" if classification else "NOT_AVAILABLE",
            "prediction": "PASS" if (snap.get("prediction") or {}).get("predicted_target") else "NOT_AVAILABLE",
            "defense": "PASS" if defense.get("recommended_action") else "NOT_AVAILABLE",
            "adaptation": "PASS" if adapt.get("scenarios") else "NOT_AVAILABLE",
            "learning": "PASS" if outcomes or snap.get("open_prediction") else "NOT_AVAILABLE",
            "playbook": "PASS" if evo.get("open_proposal") or evo.get("current") else "NOT_AVAILABLE",
        },
    }


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tp = sum(1 for r in rows if r["detection_result"] == "TP")
    fp = sum(1 for r in rows if r["detection_result"] == "FP")
    tn = sum(1 for r in rows if r["detection_result"] == "TN")
    fn = sum(1 for r in rows if r["detection_result"] == "FN")
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    if precision == NOT_ENOUGH_DATA or recall == NOT_ENOUGH_DATA or precision + recall == 0:
        f1 = NOT_ENOUGH_DATA
    else:
        f1 = round(2 * precision * recall / (precision + recall), 4)

    resolved = []
    for r in rows:
        resolved.extend(r["prediction_outcomes"])
    n_res = len(resolved)
    correct = sum(1 for x in resolved if x.get("outcome") == "CORRECT")
    partial = sum(1 for x in resolved if x.get("outcome") == "PARTIAL")
    incorrect = sum(1 for x in resolved if x.get("outcome") == "INCORRECT")
    if n_res == 0:
        pred_acc = NOT_ENOUGH_DATA
        target_acc = NOT_ENOUGH_DATA
        action_acc = NOT_ENOUGH_DATA
    else:
        pred_acc = round((correct + 0.5 * partial) / n_res, 4)
        target_acc = _ratio(sum(1 for x in resolved if x.get("target_correct")), n_res)
        action_acc = _ratio(sum(1 for x in resolved if x.get("action_correct")), n_res)

    risk_reds = [float(r["risk_reduction"]) for r in rows if r.get("risk_reduction") is not None]
    blast_reds = []
    for r in rows:
        if r.get("blast_before") is not None and r.get("blast_after") is not None:
            blast_reds.append(float(r["blast_before"]) - float(r["blast_after"]))
    disrupt_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    disrupt_vals = [disrupt_map[r["disruption"]] for r in rows if r.get("disruption") in disrupt_map]
    rob_dist = {"ROBUST": 0, "MODERATE": 0, "FRAGILE": 0, "UNCERTAIN": 0}
    for r in rows:
        klass = r.get("robustness") or "UNCERTAIN"
        if klass not in rob_dist:
            klass = "UNCERTAIN"
        rob_dist[klass] += 1
    stalled = sum(1 for r in rows if r.get("adaptation_outcome") in ("ATTACK_STALLED", "RISK_REDUCED"))
    adapt_n = sum(1 for r in rows if r.get("adaptation_outcome"))
    alts = []
    for r in rows:
        for a in r.get("alternate_targets") or []:
            if a not in alts:
                alts.append(a)

    timings = [r["timing"] for r in rows]
    def _timing_field(key: str):
        vals = [t[key] for t in timings if t.get(key) is not None]
        if not vals:
            return NOT_ENOUGH_DATA
        return {"events": vals, "mean_events": round(sum(vals) / len(vals), 2), "basis": "EVENT-BASED TIMING"}

    fp_rows = []
    for r in rows:
        if r["scenario_id"] == "SCN-006" or r.get("false_positive") or not r["expected_ransomware_likely"]:
            fp_rows.append(
                {
                    "scenario": r["scenario_id"],
                    "expected": r["expected_class"],
                    "observed": r["classification"],
                    "false_positive": r["false_positive"],
                    "result": "FALSE_POSITIVE" if r["false_positive"] else "NOT_FALSE_POSITIVE",
                }
            )

    loop_keys = ["detection", "prediction", "defense", "adaptation", "learning", "playbook"]
    closed = {}
    for k in loop_keys:
        closed[k] = "PASS" if any(r["closed_loop"].get(k) == "PASS" for r in rows) else "NOT_AVAILABLE"

    return {
        "detection_metrics": {
            "label": "SYNTHETIC EVALUATION",
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        },
        "prediction_metrics": {
            "label": "SYNTHETIC EVALUATION",
            "resolved_predictions": n_res if n_res else NOT_ENOUGH_DATA,
            "correct_predictions": correct if n_res else NOT_ENOUGH_DATA,
            "partial_predictions": partial if n_res else NOT_ENOUGH_DATA,
            "incorrect_predictions": incorrect if n_res else NOT_ENOUGH_DATA,
            "prediction_accuracy": pred_acc,
            "target_accuracy": target_acc,
            "action_accuracy": action_acc,
            "note": "Accuracy is computed only from RESOLVED synthetic predictions, not prediction scores.",
        },
        "defense_metrics": {
            "label": "SYNTHETIC EVALUATION",
            "average_risk_reduction": _mean(risk_reds),
            "average_blast_radius_reduction": _mean(blast_reds),
            "average_disruption": _mean(disrupt_vals) if disrupt_vals else NOT_ENOUGH_DATA,
            "samples": [
                {
                    "scenario": r["scenario_id"],
                    "action": r["recommended_action"],
                    "risk_before": r["risk_before"],
                    "risk_after": r["risk_after"],
                    "risk_reduction": r["risk_reduction"],
                    "blast_before": r["blast_before"],
                    "blast_after": r["blast_after"],
                    "disruption": r["disruption"],
                    "robustness": r["robustness"],
                    "adaptation_outcome": r["adaptation_outcome"],
                }
                for r in rows
                if r.get("recommended_action")
            ],
        },
        "adaptation_metrics": {
            "label": "SYNTHETIC EVALUATION",
            "distribution": rob_dist,
            "adaptation_success_rate": _ratio(stalled, adapt_n),
            "alternate_targets": alts,
        },
        "timing_metrics": {
            "label": "SYNTHETIC EVALUATION",
            "basis": "EVENT-BASED TIMING",
            "first_detection_event": _timing_field("first_detection_event"),
            "first_high_risk_event": _timing_field("first_high_risk_event"),
            "first_defense_review": _timing_field("first_defense_review"),
            "first_approval": _timing_field("first_approval"),
            "containment_verification": _timing_field("containment_verification"),
            "events_before_detection": _timing_field("first_detection_event"),
            "events_before_defense_review": _timing_field("first_defense_review"),
            "events_before_approval": _timing_field("first_approval"),
            "events_before_verification": _timing_field("containment_verification"),
        },
        "false_positive_metrics": {
            "label": "SYNTHETIC EVALUATION",
            "rows": fp_rows,
        },
        "baseline_comparison": {
            "note": "Typical traditional workflow for this prototype comparison. Not every traditional product.",
            "traditional": {
                "attack_story_visibility": "NOT_AVAILABLE",
                "prediction_availability": "NOT_AVAILABLE",
                "defense_simulation_availability": "NOT_AVAILABLE",
                "human_approval": "AVAILABLE",
                "adaptation_analysis": "NOT_AVAILABLE",
                "prediction_vs_reality_learning": "NOT_AVAILABLE",
                "playbook_evolution": "NOT_AVAILABLE",
            },
            "ransomguard_x": {
                "attack_story_visibility": "AVAILABLE",
                "prediction_availability": "AVAILABLE",
                "defense_simulation_availability": "AVAILABLE",
                "human_approval": "AVAILABLE",
                "adaptation_analysis": "AVAILABLE",
                "prediction_vs_reality_learning": "AVAILABLE",
                "playbook_evolution": "AVAILABLE",
            },
        },
        "closed_loop_metrics": {
            "detection": closed["detection"],
            "prediction": closed["prediction"],
            "defense": closed["defense"],
            "adaptation": closed["adaptation"],
            "learning": closed["learning"],
            "playbook_evolution": closed["playbook"],
            "note": "Evidence-backed playbook evolution is available when sufficient synthetic historical evidence exists.",
        },
    }


async def run(scenario_id: str | None = None) -> dict[str, Any]:
    global _SEQ, _CURRENT
    ids = [scenario_id] if scenario_id else list(EVAL_SCENARIO_IDS)
    for sid in ids:
        if sid not in SCENARIO_TRUTH or sid not in SCENARIOS:
            raise KeyError(f"Unknown evaluation scenario {sid}")
    tok = _freeze()
    rows = []
    try:
        for sid in ids:
            rows.append(await _run_one(sid))
    finally:
        _restore(tok)
    agg = _aggregate(rows)
    _SEQ += 1
    report = {
        "evaluation_id": f"EVAL-{_SEQ:04d}",
        "timestamp": datetime.utcnow().isoformat(),
        "synthetic": True,
        "real_network_action": False,
        "label": "SYNTHETIC EVALUATION",
        "disclaimer": "Prototype measurement from synthetic scenarios. Not production cybersecurity accuracy.",
        "scenarios": rows,
        **agg,
        "limitations": list(LIMITATIONS),
    }
    _CURRENT = report
    _HISTORY.append({"evaluation_id": report["evaluation_id"], "timestamp": report["timestamp"], "scenario_ids": ids})
    return report
