"""Counterfactual state-transition simulations (safe, synthetic)."""
from __future__ import annotations

from typing import Any

ACTIONS = [
    "NO_ACTION",
    "REVOKE_CREDENTIALS",
    "ISOLATE_ENDPOINT",
    "BLOCK_NETWORK_PATH",
    "ISOLATE_AND_REVOKE",
]

IMPACT_UNITS = {
    "NO_ACTION": dict(systems=6, exposure=92, downtime=48, recovery=22, containment=8, impact="CRITICAL"),
    "REVOKE_CREDENTIALS": dict(systems=4, exposure=61, downtime=22, recovery=54, containment=48, impact="HIGH"),
    "ISOLATE_ENDPOINT": dict(systems=3, exposure=44, downtime=18, recovery=62, containment=64, impact="MEDIUM"),
    "BLOCK_NETWORK_PATH": dict(systems=3, exposure=48, downtime=16, recovery=60, containment=58, impact="MEDIUM"),
    "ISOLATE_AND_REVOKE": dict(systems=1, exposure=18, downtime=8, recovery=86, containment=88, impact="LOW"),
}

PATH_BY_ACTION = {
    "NO_ACTION": ["LAB-PC-21", "student.kumar", "FAC-PC-07", "FILE-SRV-01", "BACKUP-SRV-01"],
    "REVOKE_CREDENTIALS": ["LAB-PC-21", "FAC-PC-07", "FILE-SRV-01"],
    "ISOLATE_ENDPOINT": ["LAB-PC-21"],
    "BLOCK_NETWORK_PATH": ["LAB-PC-21", "student.kumar"],
    "ISOLATE_AND_REVOKE": ["LAB-PC-21"],
}


def _time_penalty(intervention_index: int) -> dict[str, float]:
    # Later intervention increases systems/exposure
    late = max(0, intervention_index - 3)
    return {
        "systems": late * 0.7,
        "exposure": late * 8.5,
        "downtime": late * 4.0,
        "containment": -late * 7.0,
        "recovery": -late * 6.0,
    }


def run(action: str, intervention_index: int, event_count: int = 8) -> dict[str, Any]:
    if action not in IMPACT_UNITS:
        action = "NO_ACTION"
    base = dict(IMPACT_UNITS[action])
    pen = _time_penalty(intervention_index)
    systems = int(min(8, max(1, round(base["systems"] + pen["systems"]))))
    exposure = int(min(99, max(6, base["exposure"] + pen["exposure"])))
    downtime = int(min(72, max(2, base["downtime"] + pen["downtime"])))
    containment = int(min(96, max(4, base["containment"] + pen["containment"])))
    recovery = int(min(95, max(10, base["recovery"] + pen["recovery"])))
    if containment >= 80:
        impact = "LOW"
    elif containment >= 55:
        impact = "MEDIUM"
    elif containment >= 30:
        impact = "HIGH"
    else:
        impact = "CRITICAL"

    path = list(PATH_BY_ACTION[action])
    if intervention_index >= 5 and action != "NO_ACTION":
        if "FAC-PC-07" not in path:
            path.append("FAC-PC-07")
        systems = min(8, systems + 1)

    return {
        "action": action,
        "intervention_index": intervention_index,
        "systems_affected": systems,
        "affected_assets": path,
        "exposure": exposure,
        "downtime": downtime,
        "impact_level": impact,
        "containment": containment,
        "recovery": recovery,
        "label": "SIMULATED / ESTIMATED",
        "simulated": True,
    }


def run_all(intervention_index: int) -> list[dict[str, Any]]:
    return [run(a, intervention_index) for a in ACTIONS]


def alternate_realities(actual_action: str, intervention_index: int) -> dict[str, Any]:
    actual = run(actual_action or "NO_ACTION", intervention_index)
    a = run("REVOKE_CREDENTIALS", max(0, intervention_index - 1))
    b = run("ISOLATE_ENDPOINT", max(0, intervention_index - 1))
    c = run("ISOLATE_AND_REVOKE", 2)
    return {
        "actual_reality": actual,
        "scenario_a": {**a, "name": "SCENARIO A — Revoke earlier"},
        "scenario_b": {**b, "name": "SCENARIO B — Isolate endpoint"},
        "scenario_c": {**c, "name": "SCENARIO C — Isolate + revoke at 10:03"},
        "label": "SIMULATED / ESTIMATED",
    }


def missed_impact(actual: dict[str, Any], best: dict[str, Any]) -> dict[str, Any]:
    return {
        "avoidable_systems": max(0, actual["systems_affected"] - best["systems_affected"]),
        "avoidable_exposure": max(0, actual["exposure"] - best["exposure"]),
        "avoidable_downtime": max(0, actual["downtime"] - best["downtime"]),
        "estimated_avoidable_impact": max(0, actual["exposure"] - best["exposure"]),
        "actual_action": actual["action"],
        "best_action": best["action"],
        "label": "SIMULATED ESTIMATE",
        "simulated": True,
    }


def defense_regret(actual: dict[str, Any], best: dict[str, Any]) -> dict[str, Any]:
    gap = max(0, best["containment"] - actual["containment"])
    score = round(min(100, gap * 1.15 + max(0, actual["systems_affected"] - best["systems_affected"]) * 8), 1)
    reason = (
        f"Actual response {actual['action']} contained {actual['containment']} vs best feasible "
        f"{best['action']} at {best['containment']}. Gap is a simulated regret score, not a real loss."
    )
    return {
        "defense_regret_score": score,
        "reason": reason,
        "actual": actual["action"],
        "best_feasible": best["action"],
        "label": "SIMULATED ESTIMATE",
    }
