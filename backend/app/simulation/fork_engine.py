"""Read-only attack-fork projections. Never mutates live SimulationState."""
from __future__ import annotations

import copy
from typing import Any

from app.attack_graph.engine import build as build_attack_graph
from app.defense.containment import adjust_detection, apply
from app.defense.engine import ADAPTIVE_OPTIONS, CHAIN, CRIT, DISRUPT_PENALTY
from app.detection.engine import detect
from app.prediction.engine import REACHABLE_FROM, forecast

EMPTY = {
    "current_state": {
        "risk": 0,
        "current_node": None,
        "predicted_target": None,
        "attack_stage": "NORMAL",
        "blast_radius": 0,
    },
    "forks": [],
    "best_fork": None,
    "simulated": True,
    "live_state_mutated": False,
    "label": "SIMULATED attack forks — not applied",
}


def _blast(graph: dict[str, Any], protected: set[str] | None = None) -> int:
    protected = protected or set()
    nodes = {n["id"]: n for n in (graph or {}).get("nodes") or []}
    current = graph.get("current_node")
    pos = CHAIN.index(current) if current in CHAIN else 0
    remaining = CHAIN[pos:] if current else list(CHAIN)
    exposed = []
    for nid in remaining:
        if nid in protected:
            continue
        status = (nodes.get(nid) or {}).get("status", "NORMAL")
        if status == "PROTECTED":
            continue
        exposed.append(nid)
    return len(exposed)


def _adapt_next(current: str | None, predicted: str | None, protected: set[str]) -> str | None:
    if predicted and predicted not in protected:
        return predicted
    order = []
    for nid in REACHABLE_FROM.get(current, CHAIN):
        if nid not in order:
            order.append(nid)
    for nid in CHAIN:
        if nid not in order:
            order.append(nid)
    cur_i = CHAIN.index(current) if current in CHAIN else -1
    for nid in order:
        if nid in protected:
            continue
        if nid == current:
            continue
        if cur_i >= 0 and nid in CHAIN and CHAIN.index(nid) <= cur_i:
            continue
        return nid
    return None


def _summary(opt: dict[str, Any], predicted: str | None, next_target: str | None, protected: list[str]) -> str:
    name = opt.get("title") or opt.get("action")
    asset = ", ".join(protected) or "no asset"
    if predicted and predicted in protected:
        return (
            f"{name} protects the predicted target {predicted}. "
            f"Simulated attacker may redirect toward {next_target or 'NONE'}."
        )
    return (
        f"{name} protects {asset} with {opt.get('operational_disruption') or opt.get('disruption', 'MEDIUM')} "
        f"disruption. Projected next target: {next_target or 'NONE'}."
    )


def _fork_score(
    risk_reduction: float,
    blast_cut: int,
    predicted: str | None,
    protected: set[str],
    disruption: str,
    recovery: float,
) -> float:
    pred_hit = 18.0 if predicted in protected else 0.0
    crit = 12.0 if any(CRIT.get(a) == "CRITICAL" for a in protected) else 4.0
    recovery_w = recovery if ("BACKUP-SRV-01" in protected or predicted in protected) else recovery * 0.4
    score = (
        22.0
        + 0.72 * risk_reduction
        + 11.0 * blast_cut
        + pred_hit
        + crit
        + 0.28 * recovery_w
        - 0.5 * DISRUPT_PENALTY.get(disruption, 20)
    )
    return float(max(8, min(96, round(score, 1))))


def build(state: dict[str, Any] | None) -> dict[str, Any]:
    """Project independent defensive futures from a copy of live state."""
    src = copy.deepcopy(state or {})
    events = list(src.get("events") or [])
    graph = src.get("attack_graph") or {}
    detection = src.get("detection") or {}
    pred = src.get("prediction") or {}
    defense = src.get("defense") or {}
    current_node = graph.get("current_node")
    predicted = pred.get("predicted_target")
    stage = detection.get("attack_stage") or src.get("current_stage") or "NORMAL"
    current_risk = float(src.get("risk_score") or detection.get("risk_score") or 0)
    blast_before = _blast(graph)
    current_state = {
        "risk": current_risk,
        "current_node": current_node,
        "predicted_target": predicted,
        "attack_stage": stage,
        "blast_radius": blast_before,
        "attack_path": list(graph.get("attack_path") or []),
    }
    if not events:
        out = dict(EMPTY)
        out["current_state"] = current_state
        return out

    options = list(defense.get("options") or [])
    if not options:
        options = [
            {
                "action": o["action"],
                "title": o["title"],
                "operational_disruption": o["disruption"],
                "reversibility": o["reversible"],
                "defense_score": 0,
            }
            for o in ADAPTIVE_OPTIONS
        ]

    forks: list[dict[str, Any]] = []
    catalog = {o["action"]: o for o in ADAPTIVE_OPTIONS}
    for idx, opt in enumerate(options):
        action = opt.get("action")
        spec = catalog.get(action, {})
        applied = apply(action, graph)
        fork_graph = build_attack_graph(copy.deepcopy(events), copy.deepcopy(detection), applied)
        det = detect(copy.deepcopy(events))
        det = adjust_detection(det, applied)
        fc = forecast(copy.deepcopy(events), fork_graph, det.get("public") or {}, True)
        protected = set(applied.get("protected_assets") or [])
        next_target = _adapt_next(current_node, fc.get("predicted_target") or predicted, protected)
        blast_after = _blast(fork_graph, protected)
        projected_risk = float(det.get("risk_score") or current_risk)
        if projected_risk > current_risk:
            projected_risk = current_risk
        risk_reduction = round(max(0.0, current_risk - projected_risk), 1)
        disruption = opt.get("operational_disruption") or spec.get("disruption", "MEDIUM")
        remaining = [
            n["id"]
            for n in fork_graph.get("nodes") or []
            if n.get("status") not in ("PROTECTED",) and n["id"] in CHAIN[CHAIN.index(current_node) :]
        ] if current_node in CHAIN else [
            n["id"] for n in fork_graph.get("nodes") or [] if n.get("status") not in ("PROTECTED", "NORMAL")
        ]
        recovery = float(spec.get("recovery") or 16)
        score = _fork_score(risk_reduction, max(0, blast_before - blast_after), predicted, protected, disruption, recovery)
        pred_hit = predicted in protected
        containment_probability = float(
            max(22, min(92, round(46 + 0.35 * risk_reduction + (12 if pred_hit else 0) + 0.1 * recovery, 1)))
        )
        forks.append(
            {
                "fork_id": f"FORK-{idx + 1}",
                "label": chr(ord("A") + idx),
                "defense_action": action,
                "title": opt.get("title") or spec.get("title") or action,
                "projected_risk": projected_risk,
                "risk_before": current_risk,
                "risk_reduction": risk_reduction,
                "blast_radius_before": blast_before,
                "blast_radius_after": blast_after,
                "projected_blast_radius": blast_after,
                "protected_assets": list(applied.get("protected_assets") or []),
                "remaining_at_risk_assets": remaining,
                "projected_current_node": current_node,
                "projected_next_target": next_target,
                "projected_attack_stage": stage,
                "containment_probability": containment_probability,
                "operational_disruption": disruption,
                "reversibility": opt.get("reversibility") or spec.get("reversible", "YES"),
                "defense_score": opt.get("defense_score") or score,
                "fork_score": score,
                "prediction_aligned": pred_hit,
                "summary": _summary(opt, predicted, next_target, list(protected)),
                "simulated": True,
                "applied": False,
            }
        )

    forks.sort(key=lambda f: f["fork_score"], reverse=True)
    for i, fork in enumerate(forks):
        fork["fork_id"] = f"FORK-{i + 1}"
        fork["label"] = chr(ord("A") + i)
        fork["is_best"] = i == 0
    best = forks[0] if forks else None
    if best:
        why = best["summary"]
        if best.get("prediction_aligned"):
            why = (
                f"Protecting the predicted critical target reduces both risk and blast radius "
                f"with {best['operational_disruption'].lower()} operational disruption."
            )
        best = {**best, "why": why}

    return {
        "current_state": current_state,
        "forks": forks,
        "best_fork": best,
        "simulated": True,
        "live_state_mutated": False,
        "label": "SIMULATED attack forks — not applied",
    }
