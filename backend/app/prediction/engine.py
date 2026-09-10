"""Next-target prediction with optional Random Forest and deterministic fallback."""
from __future__ import annotations

from typing import Any

from app.graph.engine import build_graph
import networkx as nx

from app.paths import repo_root

ROOT = repo_root()
MODEL_PATH = ROOT / "ml" / "models" / "target_rf.joblib"

CANDIDATES = ["FILE-SRV-01", "BACKUP-SRV-01", "FAC-PC-07", "ERP-SRV-01", "LMS-SRV-01"]
CRITICALITY = {
    "FAC-PC-07": 45,
    "FILE-SRV-01": 75,
    "BACKUP-SRV-01": 95,
    "ERP-SRV-01": 95,
    "LMS-SRV-01": 95,
}


def _stage_bias(stage: str, target: str) -> float:
    mapping = {
        "NORMAL": {"FAC-PC-07": 20},
        "INITIAL_ACCESS": {"FAC-PC-07": 35, "FILE-SRV-01": 20},
        "EXECUTION": {"FAC-PC-07": 30, "FILE-SRV-01": 28},
        "IMPACT_PREP": {"FAC-PC-07": 30, "FILE-SRV-01": 28},
        "CREDENTIAL_ACCESS": {"FAC-PC-07": 40, "FILE-SRV-01": 32},
        "PRIVILEGE_ESCALATION": {"FAC-PC-07": 48, "FILE-SRV-01": 40},
        "LATERAL_MOVEMENT": {"FILE-SRV-01": 55, "BACKUP-SRV-01": 30, "ERP-SRV-01": 22},
        "DATA_ACCESS": {"BACKUP-SRV-01": 60, "ERP-SRV-01": 28, "FILE-SRV-01": 20},
        "COLLECTION": {"BACKUP-SRV-01": 60, "ERP-SRV-01": 28, "FILE-SRV-01": 20},
        "RANSOMWARE_IMPACT": {"BACKUP-SRV-01": 70, "ERP-SRV-01": 24},
        "INHIBIT_RECOVERY": {"BACKUP-SRV-01": 70, "ERP-SRV-01": 24},
    }
    return mapping.get(stage, {}).get(target, 8.0)


def _reachability(current: str, target: str) -> float:
    g = build_graph()
    if not current or current not in g or target not in g:
        return 10.0
    if nx.has_path(g, current, target):
        length = nx.shortest_path_length(g, current, target)
        return max(8.0, 42 - 8 * length)
    return 6.0


def _event_bias(events: list[dict[str, Any]], target: str) -> float:
    types = {e.get("event_type") for e in events}
    score = 0.0
    if "lateral_movement" in types and target in ("FILE-SRV-01", "FAC-PC-07"):
        score += 18
    if "file_server_access" in types and target == "BACKUP-SRV-01":
        score += 26
    if "privilege_escalation" in types and target == "FAC-PC-07":
        score += 12
    if "backup_access_attempt" in types and target == "BACKUP-SRV-01":
        score += 10
    return score


def predict(
    events: list[dict[str, Any]],
    stage: str,
    current_position: str,
    contained: bool = False,
) -> list[dict[str, Any]]:
    if not events:
        return []
    results = []
    for target in CANDIDATES:
        raw = (
            0.28 * _reachability(current_position or "LAB-PC-21", target)
            + 0.22 * (CRITICALITY[target] / 2)
            + 0.30 * _stage_bias(stage, target)
            + 0.20 * _event_bias(events, target)
        )
        if contained and target in ("FILE-SRV-01", "BACKUP-SRV-01", "ERP-SRV-01"):
            raw *= 0.35
        conf = float(max(5, min(96, raw)))
        results.append(
            {
                "predicted_target": target,
                "confidence": round(conf, 1),
                "confidence_range": [round(max(0, conf - 3.2), 1), round(min(99, conf + 3.1), 1)],
                "prediction_lead_time": "2-6 simulated minutes",
                "reasons": _reasons(target, stage, events),
                "model": "deterministic_weighted",
                "simulated": True,
            }
        )
    results.sort(key=lambda x: x["confidence"], reverse=True)

    try:
        if MODEL_PATH.exists():
            import joblib

            model = joblib.load(MODEL_PATH)
            vec = _vector(events, stage)
            proba = model.predict_proba(vec)[0]
            classes = list(model.classes_)
            for row in results:
                if row["predicted_target"] in classes:
                    p = float(proba[classes.index(row["predicted_target"])] * 100)
                    row["confidence"] = round(0.55 * row["confidence"] + 0.45 * p, 1)
                    row["model"] = "random_forest+deterministic"
            results.sort(key=lambda x: x["confidence"], reverse=True)
    except Exception:
        pass
    return results


def _reasons(target: str, stage: str, events: list[dict[str, Any]]) -> list[str]:
    reasons = [f"Attack stage {stage} increases likelihood of {target}"]
    if target == "FILE-SRV-01":
        reasons.append("Faculty host FAC-PC-07 can access the file server")
    if target == "BACKUP-SRV-01":
        reasons.append("Backup disruption is a common ransomware recovery-inhibition step")
    if target == "ERP-SRV-01":
        reasons.append("ERP is reachable from faculty segment but lower on this path")
    if any(e.get("event_type") == "lateral_movement" for e in events):
        reasons.append("Observed lateral movement expands reachable high-value assets")
    return reasons


def _vector(events: list[dict[str, Any]], stage: str):
    import numpy as np

    types = [e.get("event_type") for e in events]
    feats = [
        float(types.count("suspicious_process")),
        float(types.count("mass_file_modification")),
        float(types.count("credential_access")),
        float(types.count("privilege_escalation")),
        float(types.count("lateral_movement")),
        float(types.count("file_server_access")),
        float(types.count("backup_access_attempt")),
        float(hash(stage) % 7),
    ]
    return np.array(feats, dtype=float).reshape(1, -1)


def train_rf() -> dict[str, Any]:
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    import joblib

    rng = np.random.default_rng(7)
    X = []
    y = []
    mapping = {
        0: "FAC-PC-07",
        1: "FILE-SRV-01",
        2: "BACKUP-SRV-01",
        3: "ERP-SRV-01",
        4: "LMS-SRV-01",
    }
    for _ in range(200):
        vec = rng.poisson(0.8, size=8).astype(float)
        label_idx = int(np.clip(vec[4] + vec[5] + 0.5 * vec[6], 0, 4))
        X.append(vec)
        y.append(mapping[label_idx])
    model = RandomForestClassifier(n_estimators=60, random_state=7)
    model.fit(np.array(X), np.array(y))
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    return {"trained": True, "path": str(MODEL_PATH)}


PHASE4_TARGETS = ["LAB-PC-21", "student.kumar", "FAC-PC-07", "FILE-SRV-01", "BACKUP-SRV-01"]
CRIT = {
    "LAB-PC-21": "MEDIUM",
    "student.kumar": "HIGH",
    "FAC-PC-07": "HIGH",
    "FILE-SRV-01": "CRITICAL",
    "BACKUP-SRV-01": "CRITICAL",
}
EMPTY_FORECAST = {
    "predicted_target": None,
    "predicted_action": None,
    "confidence": 0,
    "reason": "",
    "evidence": [],
    "alternatives": [],
    "current_node": None,
    "current_stage": "NORMAL",
    "ranked": [],
    "label": "SIMULATED prediction",
    "simulated": True,
}

# Deterministic next hop after the latest observed event.
NEXT_BY_LAST_EVENT = {
    "suspicious_process": ("LAB-PC-21", "MASS_FILE_MODIFICATION"),
    "mass_file_modification": ("LAB-PC-21", "RAPID_FILE_RENAME"),
    "rapid_file_rename": ("student.kumar", "CREDENTIAL_ACCESS"),
    "credential_access": ("student.kumar", "PRIVILEGE_ESCALATION"),
    "privilege_escalation": ("FAC-PC-07", "LATERAL_MOVEMENT"),
    "lateral_movement": ("FILE-SRV-01", "FILE_SERVER_ACCESS"),
    "file_server_access": ("BACKUP-SRV-01", "BACKUP_ACCESS"),
    "backup_access_attempt": ("BACKUP-SRV-01", "RANSOMWARE_IMPACT"),
}

REACHABLE_FROM = {
    "LAB-PC-21": ["LAB-PC-21", "student.kumar", "FAC-PC-07"],
    "student.kumar": ["student.kumar", "FAC-PC-07", "FILE-SRV-01"],
    "FAC-PC-07": ["FAC-PC-07", "FILE-SRV-01", "BACKUP-SRV-01"],
    "FILE-SRV-01": ["FILE-SRV-01", "BACKUP-SRV-01"],
    "BACKUP-SRV-01": ["BACKUP-SRV-01"],
    None: ["LAB-PC-21"],
}


def _empty_forecast(stage: str = "NORMAL", current: str | None = None) -> dict[str, Any]:
    out = dict(EMPTY_FORECAST)
    out["current_stage"] = stage or "NORMAL"
    out["current_node"] = current
    return out


def forecast(
    events: list[dict[str, Any]],
    graph: dict[str, Any] | None,
    detection: dict[str, Any] | None = None,
    contained: bool = False,
    memory_adjustments: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Deterministic next-target / next-action forecast from live state."""
    graph = graph or {}
    detection = detection or {}
    stage = detection.get("attack_stage") or "NORMAL"
    current = graph.get("current_node")
    path = list(graph.get("attack_path") or [])
    nodes = {n["id"]: n for n in graph.get("nodes") or []}
    if not events:
        return _empty_forecast(stage, current)

    last = events[-1].get("event_type")
    designated_target, designated_action = NEXT_BY_LAST_EVENT.get(last, (None, None))
    types = [e.get("event_type") for e in events]
    reachable = set(REACHABLE_FROM.get(current, PHASE4_TARGETS))
    scored = []
    for target in PHASE4_TARGETS:
        if target not in reachable:
            continue
        node = nodes.get(target, {})
        status = node.get("status", "NORMAL")
        if status == "PROTECTED":
            continue
        compromised = bool(node.get("compromised"))
        already_reached = target in path
        score = 12.0
        if target == designated_target:
            score += 48
        if CRIT[target] == "CRITICAL":
            score += 18
        elif CRIT[target] == "HIGH":
            score += 12
        else:
            score += 6
        if already_reached and compromised and target != designated_target:
            continue
        if already_reached and compromised and target == designated_target:
            score += 8  # same-asset follow-on (priv-esc / impact)
        if not already_reached:
            score += 16
        if status == "AT_RISK" and target == designated_target:
            score += 10
        if "lateral_movement" in types and target == "FILE-SRV-01":
            score += 14
        if "file_server_access" in types and target == "BACKUP-SRV-01":
            score += 16
        if contained and target in ("FILE-SRV-01", "BACKUP-SRV-01"):
            score *= 0.4
        adj = float((memory_adjustments or {}).get(target, 0) or 0)
        adj = max(-10.0, min(10.0, adj))
        score = float(max(8, min(96, round(score + adj, 1))))
        action = designated_action if target == designated_target else _action_for_target(target, last)
        scored.append(
            {
                "predicted_target": target,
                "predicted_action": action,
                "prediction_score": score,
                "confidence": score,
                "name": node.get("name", target),
            }
        )
    scored.sort(key=lambda x: x["prediction_score"], reverse=True)
    if not scored:
        return _empty_forecast(stage, current)

    primary = scored[0]
    # Prefer designated target if present in scored list
    for row in scored:
        if row["predicted_target"] == designated_target:
            primary = row
            break
    alternatives = [r for r in scored if r["predicted_target"] != primary["predicted_target"]][:3]
    evidence = _forecast_evidence(types, nodes, current, primary["predicted_target"], graph)
    reason = _forecast_reason(current, primary["predicted_target"], primary["predicted_action"], nodes)
    ranked = [
        {
            "predicted_target": r["predicted_target"],
            "confidence": r["confidence"],
            "predicted_action": r["predicted_action"],
            "reasons": [reason],
            "model": "deterministic_weighted",
            "simulated": True,
        }
        for r in [primary] + alternatives
    ]
    return {
        "predicted_target": primary["predicted_target"],
        "predicted_action": primary["predicted_action"],
        "confidence": primary["confidence"],
        "reason": reason,
        "evidence": evidence,
        "alternatives": [
            {
                "predicted_target": a["predicted_target"],
                "predicted_action": a["predicted_action"],
                "confidence": a["confidence"],
                "prediction_score": a["prediction_score"],
            }
            for a in alternatives
        ],
        "current_node": current,
        "current_stage": stage,
        "ranked": ranked,
        "label": "SIMULATED prediction — not real-world accuracy",
        "simulated": True,
    }


def _action_for_target(target: str, last_event: str) -> str:
    mapping = {
        "LAB-PC-21": "MASS_FILE_MODIFICATION",
        "student.kumar": "CREDENTIAL_ACCESS",
        "FAC-PC-07": "LATERAL_MOVEMENT",
        "FILE-SRV-01": "FILE_SERVER_ACCESS",
        "BACKUP-SRV-01": "BACKUP_ACCESS",
    }
    if last_event == "backup_access_attempt":
        return "RANSOMWARE_IMPACT"
    return mapping.get(target, "LATERAL_MOVEMENT")


def _forecast_evidence(
    types: list[str],
    nodes: dict[str, Any],
    current: str | None,
    target: str,
    graph: dict[str, Any],
) -> list[str]:
    evidence = []
    if types:
        evidence.append(f"{types[-1]} observed")
    if current:
        st = (nodes.get(current) or {}).get("status")
        if st:
            evidence.append(f"{current} status is {st}")
    if current:
        evidence.append(f"current attacker position is {current}")
    edges = graph.get("edges") or []
    for e in edges:
        if e.get("target") == target and e.get("observed"):
            evidence.append(f"{e['type']} toward {target} already observed")
        if e.get("source") == current and e.get("target") == target:
            evidence.append(f"{target} is reachable from {current}")
    crit = CRIT.get(target)
    if crit:
        evidence.append(f"{target} criticality is {crit}")
    return evidence


def _forecast_reason(current: str | None, target: str, action: str, nodes: dict[str, Any]) -> str:
    crit = CRIT.get(target, "UNKNOWN")
    cur = current or "an unreached origin"
    tname = (nodes.get(target) or {}).get("name", target)
    return (
        f"The attack has reached {cur} and {tname} is the next scored reachable asset "
        f"(criticality {crit}). Predicted synthetic action: {action}."
    )

