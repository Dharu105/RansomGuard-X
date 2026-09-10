"""Defense recommendation, scoring, and simulated containment."""
from __future__ import annotations

from typing import Any

from app.defense import containment as containment_engine
from app.defense.models import EMPTY_DEFENSE

ACTIONS = [
    "NO_ACTION",
    "REVOKE_CREDENTIALS",
    "ISOLATE_ENDPOINT",
    "BLOCK_NETWORK_PATH",
    "ISOLATE_AND_REVOKE",
    "EMERGENCY_SERVER_SHUTDOWN",
]


def _metrics(action: str, risk: float, stage: str, memory_boost: dict[str, float] | None = None) -> dict[str, Any]:
    table = {
        "NO_ACTION": dict(containment=8, downtime=0, business_impact=6, residual_risk=92, recovery=18, asset_protection=10),
        "REVOKE_CREDENTIALS": dict(containment=48, downtime=12, business_impact=18, residual_risk=54, recovery=55, asset_protection=50),
        "ISOLATE_ENDPOINT": dict(containment=62, downtime=22, business_impact=24, residual_risk=42, recovery=60, asset_protection=64),
        "BLOCK_NETWORK_PATH": dict(containment=58, downtime=18, business_impact=20, residual_risk=46, recovery=58, asset_protection=61),
        "ISOLATE_AND_REVOKE": dict(containment=88, downtime=28, business_impact=32, residual_risk=18, recovery=82, asset_protection=86),
        "EMERGENCY_SERVER_SHUTDOWN": dict(containment=90, downtime=78, business_impact=86, residual_risk=14, recovery=70, asset_protection=88),
    }
    m = dict(table[action])
    if stage in ("LATERAL_MOVEMENT", "COLLECTION", "INHIBIT_RECOVERY") and action == "NO_ACTION":
        m["residual_risk"] = min(99, m["residual_risk"] + 6)
        m["containment"] = max(2, m["containment"] - 4)
    if risk < 35 and action == "EMERGENCY_SERVER_SHUTDOWN":
        m["business_impact"] += 10
    if memory_boost and action in memory_boost:
        m["containment"] = min(96, m["containment"] + memory_boost[action])
    overall = round(
        0.34 * m["containment"]
        + 0.18 * (100 - m["business_impact"])
        + 0.16 * m["recovery"]
        + 0.18 * m["asset_protection"]
        + 0.14 * (100 - m["residual_risk"]),
        1,
    )
    conf = min(96.0, 54 + m["containment"] * 0.35)
    return {
        "action": action,
        "containment": m["containment"],
        "downtime": m["downtime"],
        "business_impact": m["business_impact"],
        "residual_risk": m["residual_risk"],
        "recovery_probability": m["recovery"],
        "asset_protection": m["asset_protection"],
        "business_continuity": 100 - m["business_impact"],
        "overall_defense_score": overall,
        "confidence": round(conf, 1),
        "confidence_range": [round(conf - 4.5, 1), round(min(99, conf + 4.2), 1)],
        "simulated": True,
        "label": "SIMULATED / ESTIMATED",
    }


def recommend(
    risk: float,
    stage: str,
    intent: str,
    memory: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    memory_boost: dict[str, float] = {}
    if memory:
        for row in memory:
            if row.get("decision_quality") in ("good", "excellent"):
                memory_boost[row.get("defense_used", "")] = memory_boost.get(row.get("defense_used", ""), 0) + 4

    options = [_metrics(a, risk, stage, memory_boost) for a in ACTIONS]
    # Maximize containment while penalizing unnecessary disruption
    def key(o: dict[str, Any]) -> float:
        disruption_penalty = 0.0
        if risk < 50 and o["action"] == "EMERGENCY_SERVER_SHUTDOWN":
            disruption_penalty = 25
        if risk < 30 and o["action"] not in ("NO_ACTION", "REVOKE_CREDENTIALS"):
            disruption_penalty = 12
        return o["overall_defense_score"] - disruption_penalty

    ranked = sorted(options, key=key, reverse=True)
    recommended = ranked[0]
    if risk >= 55 and recommended["action"] == "NO_ACTION":
        recommended = next(o for o in ranked if o["action"] == "ISOLATE_AND_REVOKE")
    explanation = _explain(recommended, risk, stage, intent)
    approval_required = _approval_gate(risk)
    return {
        "options": ranked,
        "recommended_defense": recommended,
        "explanation": explanation,
        "approval_gate": approval_required,
        "simulated": True,
    }


def _explain(rec: dict[str, Any], risk: float, stage: str, intent: str) -> str:
    return (
        f"Selected {rec['action']} because simulated containment is {rec['containment']} "
        f"with residual risk {rec['residual_risk']}. Current stage {stage} and intent {intent} "
        f"at risk {risk}. Isolation plus credential revocation maximizes containment of LAB-PC-21 "
        f"without shutting down campus servers."
    )


def _approval_gate(risk: float) -> dict[str, Any]:
    if risk <= 30:
        return {"level": "LOW", "mode": "automatic", "required": False}
    if risk <= 60:
        return {"level": "MEDIUM", "mode": "analyst", "required": True}
    if risk <= 80:
        return {"level": "HIGH", "mode": "mandatory_human", "required": True}
    return {"level": "CRITICAL", "mode": "security_administrator", "required": True}


def simulate_containment(action: str, graph: dict[str, Any]) -> dict[str, Any]:
    if action in containment_engine.EFFECTS:
        return containment_engine.apply(action, graph)
    isolated = []
    revoked = []
    blocked = []
    protected = []
    if action in ("ISOLATE_ENDPOINT", "ISOLATE_AND_REVOKE", "EMERGENCY_SERVER_SHUTDOWN", "ISOLATE_LAB_PC"):
        isolated = ["LAB-PC-21"]
        blocked = ["LAB-PC-21->FAC-PC-07"]
    if action in ("REVOKE_CREDENTIALS", "ISOLATE_AND_REVOKE", "DISABLE_STUDENT_ACCOUNT"):
        revoked = ["CRED-STU-21", "student.kumar"]
    if action == "BLOCK_NETWORK_PATH":
        blocked = ["LAB-PC-21->FAC-PC-07", "FAC-PC-07->FILE-SRV-01"]
    if action == "EMERGENCY_SERVER_SHUTDOWN":
        isolated += ["FILE-SRV-01"]
    if action == "PROTECT_FILE_SERVER":
        protected = ["FILE-SRV-01"]
        blocked = ["FAC-PC-07->FILE-SRV-01"]
    if action == "PROTECT_BACKUP_SERVER":
        protected = ["BACKUP-SRV-01"]
        blocked = ["FILE-SRV-01->BACKUP-SRV-01"]
    if action == "ISOLATE_FACULTY_PC":
        isolated = ["FAC-PC-07"]
        blocked = ["FAC-PC-07->FILE-SRV-01"]
    if action not in ("NO_ACTION", None, "") and not protected:
        protected = ["FILE-SRV-01", "BACKUP-SRV-01"]
    contained = action != "NO_ACTION"
    return {
        "contained": contained,
        "action": action,
        "isolated_assets": isolated,
        "revoked_credentials": revoked,
        "blocked_paths": blocked,
        "protected_assets": protected,
        "attacker_position": "LAB-PC-21" if contained else graph.get("current_position"),
        "propagation_stopped": contained,
        "notes": [
            "LAB-PC-21 isolated" if isolated else "No isolation",
            "student credential revoked" if revoked else "Credentials remain valid",
            "lateral path blocked" if blocked else "Lateral path open",
            "file server protected" if "FILE-SRV-01" in protected else "file server unprotected",
            "backup server protected" if "BACKUP-SRV-01" in protected else "backup unprotected",
        ],
        "simulated": True,
        "real_network_action": False,
    }


CHAIN = ["LAB-PC-21", "student.kumar", "FAC-PC-07", "FILE-SRV-01", "BACKUP-SRV-01"]
CRIT = {
    "LAB-PC-21": "MEDIUM",
    "student.kumar": "HIGH",
    "FAC-PC-07": "HIGH",
    "FILE-SRV-01": "CRITICAL",
    "BACKUP-SRV-01": "CRITICAL",
}
DISRUPT_PENALTY = {"LOW": 8, "MEDIUM": 24, "HIGH": 42}

# Catalog of SAFE simulated projections only. Never mapped to real controls.
ADAPTIVE_OPTIONS = [
    {
        "action": "ISOLATE_LAB_PC",
        "title": "Isolate endpoint",
        "description": "Reduce simulated attack propagation from LAB-PC-21.",
        "protects": ["LAB-PC-21"],
        "block_index": 0,
        "disruption": "MEDIUM",
        "reversible": "YES",
        "recovery": 16,
        "base_cut": 30,
    },
    {
        "action": "DISABLE_STUDENT_ACCOUNT",
        "title": "Disable compromised account",
        "description": "Reduce simulated credential-based propagation from the student account.",
        "protects": ["student.kumar"],
        "block_index": 1,
        "disruption": "MEDIUM",
        "reversible": "YES",
        "recovery": 18,
        "base_cut": 28,
    },
    {
        "action": "ISOLATE_FACULTY_PC",
        "title": "Isolate faculty host",
        "description": "Reduce simulated lateral reach from FAC-PC-07 toward campus servers.",
        "protects": ["FAC-PC-07"],
        "block_index": 2,
        "disruption": "MEDIUM",
        "reversible": "YES",
        "recovery": 20,
        "base_cut": 26,
    },
    {
        "action": "PROTECT_FILE_SERVER",
        "title": "Protect file server",
        "description": "Reduce simulated probability of FILE-SRV-01 compromise.",
        "protects": ["FILE-SRV-01"],
        "block_index": 3,
        "disruption": "LOW",
        "reversible": "YES",
        "recovery": 32,
        "base_cut": 26,
    },
    {
        "action": "PROTECT_BACKUP_SERVER",
        "title": "Protect backup",
        "description": "Reduce simulated backup impact and preserve recovery options.",
        "protects": ["BACKUP-SRV-01"],
        "block_index": 4,
        "disruption": "LOW",
        "reversible": "YES",
        "recovery": 46,
        "base_cut": 20,
    },
]


def _pos(node: str | None) -> int:
    if node in CHAIN:
        return CHAIN.index(node)
    return 0


def _blast_before(current: str | None, path: list[str]) -> int:
    if not path and not current:
        return 0
    pos = _pos(current)
    return max(1, len(CHAIN) - pos - 1) if pos < len(CHAIN) - 1 else 1


def recommend_adaptive(
    events: list[dict[str, Any]],
    graph: dict[str, Any] | None,
    detection: dict[str, Any] | None,
    forecast: dict[str, Any] | None,
    contained: bool = False,
) -> dict[str, Any]:
    """Deterministic multi-option defense scoring from live synthetic state."""
    graph = graph or {}
    detection = detection or {}
    forecast = forecast or {}
    if not events:
        empty = dict(EMPTY_DEFENSE)
        empty["current_node"] = graph.get("current_node")
        empty["predicted_target"] = None
        return empty

    risk_before = float(detection.get("risk_score") or 0)
    stage = detection.get("attack_stage") or "NORMAL"
    current = graph.get("current_node")
    path = list(graph.get("attack_path") or [])
    predicted = forecast.get("predicted_target")
    pred_action = forecast.get("predicted_action")
    pred_conf = float(forecast.get("confidence") or 0)
    types = [e.get("event_type") for e in events]
    blast_before = _blast_before(current, path)
    pos = _pos(current)

    scored: list[dict[str, Any]] = []
    for spec in ADAPTIVE_OPTIONS:
        distance_ahead = spec["block_index"] - pos
        if distance_ahead < 0:
            late = -distance_ahead
            timeliness = 0.32 if late == 1 else 0.18
        elif distance_ahead == 0:
            late = 0
            timeliness = 1.0
        elif distance_ahead == 1:
            late = 0
            timeliness = 0.96
        elif distance_ahead == 2:
            late = 0
            timeliness = 0.52
        else:
            late = 0
            timeliness = 0.22
        pred_hit = predicted in spec["protects"]
        if pred_hit:
            timeliness = max(timeliness, 0.94)
        pred_bonus = (22.0 + 0.14 * pred_conf) if pred_hit else 0.0

        stage_bonus = 0.0
        action = spec["action"]
        if action == "ISOLATE_LAB_PC" and stage in ("INITIAL_ACCESS", "EXECUTION"):
            stage_bonus += 18
        if action == "DISABLE_STUDENT_ACCOUNT" and stage in ("CREDENTIAL_ACCESS", "PRIVILEGE_ESCALATION"):
            stage_bonus += 20
        if action == "ISOLATE_FACULTY_PC" and stage in ("PRIVILEGE_ESCALATION", "LATERAL_MOVEMENT"):
            stage_bonus += 14
        if action == "PROTECT_FILE_SERVER" and stage in ("LATERAL_MOVEMENT", "DATA_ACCESS"):
            stage_bonus += 22
        if action == "PROTECT_BACKUP_SERVER" and stage in ("DATA_ACCESS", "RANSOMWARE_IMPACT"):
            stage_bonus += 24
        if "lateral_movement" in types and action == "PROTECT_FILE_SERVER":
            stage_bonus += 10
        if "file_server_access" in types and action == "PROTECT_BACKUP_SERVER":
            stage_bonus += 12
        if "backup_access_attempt" in types and action == "PROTECT_BACKUP_SERVER":
            stage_bonus += 8
        if pred_action == "FILE_SERVER_ACCESS" and action == "PROTECT_FILE_SERVER":
            stage_bonus += 8
        if pred_action in ("BACKUP_ACCESS", "RANSOMWARE_IMPACT") and action == "PROTECT_BACKUP_SERVER":
            stage_bonus += 8

        crit_pts = 14 if any(CRIT.get(a) == "CRITICAL" for a in spec["protects"]) else 5
        if not pred_hit and distance_ahead >= 2:
            crit_pts = 3
        recovery_w = float(spec["recovery"])
        if not pred_hit and distance_ahead >= 3:
            recovery_w *= 0.22
        elif not pred_hit and distance_ahead == 2:
            recovery_w *= 0.45
        elif distance_ahead < 0 and not pred_hit:
            recovery_w *= 0.4
        raw_cut = (spec["base_cut"] + pred_bonus * 0.5 + stage_bonus * 0.45) * timeliness
        if contained:
            raw_cut *= 0.55
        risk_reduction = float(max(2.0, min(max(0.0, risk_before - 3.0), round(raw_cut, 1))))
        if risk_before <= 0:
            risk_reduction = 0.0
        risk_after = round(max(0.0, risk_before - risk_reduction), 1)
        if risk_after > risk_before:
            risk_after = risk_before
            risk_reduction = 0.0

        blast_cut = 0
        if distance_ahead < 0:
            blast_cut = 0 if late >= 2 else 1
        elif distance_ahead == 0:
            blast_cut = 2
        elif distance_ahead == 1:
            blast_cut = 2 if pred_hit else 1
        elif distance_ahead == 2:
            blast_cut = 1 if pred_hit else 0
        else:
            blast_cut = 1 if pred_hit else 0
        if action == "PROTECT_BACKUP_SERVER" and not pred_hit and distance_ahead >= 2:
            blast_cut = 0
        blast_after = max(0, blast_before - blast_cut)
        if blast_after > blast_before:
            blast_after = blast_before

        disrupt_pen = DISRUPT_PENALTY[spec["disruption"]]
        defense_score = (
            24.0
            + 0.70 * risk_reduction
            + 12.0 * (blast_before - blast_after)
            + 0.38 * recovery_w
            + (20.0 if pred_hit else 0.0)
            + crit_pts
            - 0.55 * disrupt_pen
        )
        defense_score = float(max(8, min(96, round(defense_score, 1))))
        confidence = float(
            max(
                8,
                min(
                    96,
                    round(
                        40
                        + 0.28 * risk_reduction
                        + (0.18 * pred_conf if pred_hit else 4)
                        + 0.12 * recovery_w,
                        1,
                    ),
                ),
            )
        )
        reason = _adaptive_reason(spec, current, predicted, pred_hit, late, risk_reduction)
        scored.append(
            {
                "action": action,
                "title": spec["title"],
                "description": spec["description"],
                "risk_before": round(risk_before, 1),
                "risk_after": risk_after,
                "risk_reduction": round(risk_before - risk_after, 1),
                "blast_radius_before": int(blast_before),
                "blast_radius_after": int(blast_after),
                "operational_disruption": spec["disruption"],
                "reversibility": spec["reversible"],
                "confidence": confidence,
                "defense_score": defense_score,
                "reason": reason,
                "protects": list(spec["protects"]),
                "simulated": True,
                "real_network_action": False,
            }
        )

    scored.sort(key=lambda o: o["defense_score"], reverse=True)
    top = scored[0]
    forks = [
        {
            "id": o["action"],
            "from": "CURRENT",
            "projected_risk": o["risk_after"],
            "projected_blast": o["blast_radius_after"],
            "defense_score": o["defense_score"],
            "simulated": True,
            "note": "Independent projection only — not a full alternate-reality replay.",
        }
        for o in scored
    ]
    return {
        "recommended_action": top["action"],
        "recommended_reason": top["reason"],
        "recommended_score": top["defense_score"],
        "options": scored,
        "forks": forks,
        "current_node": current,
        "predicted_target": predicted,
        "simulated": True,
        "real_network_action": False,
        "label": "SIMULATED defense projection — no real containment",
    }


def _adaptive_reason(
    spec: dict[str, Any],
    current: str | None,
    predicted: str | None,
    pred_hit: bool,
    late: int,
    risk_reduction: float,
) -> str:
    target = spec["protects"][0]
    if pred_hit:
        return (
            f"Protecting {target} matches the predicted next target from {current or 'the current node'} "
            f"with {spec['disruption'].lower()} operational disruption and simulated risk reduction {risk_reduction}."
        )
    if late >= 2:
        return (
            f"{spec['title']} is a fallback: the simulated attacker has already moved past {target}, "
            f"so blast-radius reduction is limited compared with protecting the predicted path."
        )
    return (
        f"{spec['title']} reduces simulated propagation around {target} from {current or 'the origin'} "
        f"with {spec['disruption'].lower()} disruption (reversible={spec['reversible']})."
    )
