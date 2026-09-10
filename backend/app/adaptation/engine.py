"""Adaptive attacker simulation after a defense action."""
from __future__ import annotations

import copy
from typing import Any

from app.adaptation.models import EMPTY_ADAPTATION, LEVELS
from app.defense.containment import apply
from app.defense.engine import ADAPTIVE_OPTIONS, CHAIN, CRIT, DISRUPT_PENALTY
from app.prediction.engine import REACHABLE_FROM
from app.simulation import fork_engine


def adapt(defense_action: str, contained: bool) -> dict[str, Any]:
    original = ["LAB-PC-21", "student.kumar", "FAC-PC-07", "FILE-SRV-01", "BACKUP-SRV-01"]
    blocked: list[str] = []
    alternative: list[str] = []
    narrative = "Attacker continues original path."
    if defense_action in ("ISOLATE_ENDPOINT", "ISOLATE_AND_REVOKE") and contained:
        blocked = ["LAB-PC-21", "LAB-PC-21->FAC-PC-07"]
        alternative = ["svc.backup", "FAC-PC-07", "FILE-SRV-01"]
        narrative = (
            "After LAB-PC-21 isolation, the simulated attacker attempts a compromised service account "
            "path toward FAC-PC-07 and FILE-SRV-01."
        )
    elif defense_action == "REVOKE_CREDENTIALS":
        blocked = ["student.kumar", "CRED-STU-21"]
        alternative = ["LAB-PC-21", "stolen_token", "FAC-PC-07"]
        narrative = "Credential revocation forces a simulated token-reuse attempt from the isolated host."
    elif defense_action == "BLOCK_NETWORK_PATH":
        blocked = ["LAB-PC-21->FAC-PC-07"]
        alternative = ["LAB-PC-21", "LAB-PC-22", "ADMIN-PC-03"]
        narrative = "Blocked lab-to-faculty path; attacker probes adjacent lab host (simulated)."
    elif defense_action == "NO_ACTION":
        alternative = original
        narrative = "No defense applied. Simulated attacker remains on the original path."

    return {
        "original_path": original,
        "blocked_path": blocked,
        "alternative_path": alternative,
        "narrative": narrative,
        "adapted": bool(alternative and alternative != original),
        "simulated": True,
        "deterministic": True,
    }


def robustness_test(action: str, rates: list[int]) -> dict[str, Any]:
    """Test recommendation stability under attacker adaptation assumptions."""
    preferred = []
    for rate in rates:
        # Higher adaptation reduces isolate-only effectiveness
        isolate_score = 88 - rate * 0.28
        revoke_score = 70 - rate * 0.12
        both_score = 90 - rate * 0.10
        shutdown_score = 86 - rate * 0.05
        ranking = {
            "ISOLATE_AND_REVOKE": both_score,
            "ISOLATE_ENDPOINT": isolate_score,
            "REVOKE_CREDENTIALS": revoke_score,
            "EMERGENCY_SERVER_SHUTDOWN": shutdown_score,
            "BLOCK_NETWORK_PATH": 62 - rate * 0.18,
            "NO_ACTION": 12,
        }
        top = max(ranking, key=ranking.get)
        preferred.append({"rate": rate, "top": top, "scores": {k: round(v, 1) for k, v in ranking.items()}})

    tops = {p["top"] for p in preferred}
    if len(tops) == 1:
        verdict = "ROBUST"
    elif len(tops) == 2:
        verdict = "MODERATELY ROBUST"
    else:
        verdict = "UNCERTAIN"
    if action and action not in tops and len(tops) > 1:
        verdict = "UNCERTAIN"
    note = ""
    if verdict == "UNCERTAIN":
        note = "UNCERTAIN — HUMAN REVIEW REQUIRED"
    return {
        "action": action,
        "trials": preferred,
        "verdict": verdict,
        "note": note,
        "label": "SIMULATED robustness under adaptation assumptions",
        "simulated": True,
    }


def _reachable_alternates(current: str | None, protected: set[str], graph: dict[str, Any]) -> list[str]:
    """Graph-constrained synthetic alternates. Never invent off-graph assets."""
    nodes = {n["id"]: n for n in (graph or {}).get("nodes") or []}
    allowed = set(nodes) | set(CHAIN)
    reachable: list[str] = []
    for nid in REACHABLE_FROM.get(current, []):
        if nid not in reachable:
            reachable.append(nid)
    for edge in graph.get("edges") or []:
        src, tgt = edge.get("source"), edge.get("target")
        if src == current and tgt and tgt not in reachable:
            reachable.append(tgt)
        if src in reachable and tgt and tgt not in reachable:
            reachable.append(tgt)
    cur_i = CHAIN.index(current) if current in CHAIN else -1
    if cur_i >= 0:
        for nid in CHAIN[cur_i + 1 :]:
            if nid not in reachable:
                reachable.append(nid)
    alts = []
    for nid in reachable:
        if nid not in allowed or nid in protected or nid == current:
            continue
        if (nodes.get(nid) or {}).get("status") == "PROTECTED":
            continue
        alts.append(nid)
    return alts


def _classify(score: float, scenarios: list[dict[str, Any]], live_risk: float) -> str:
    if not scenarios or live_risk <= 0:
        return "UNCERTAIN"
    lows = scenarios[0]["projected_risk"]
    highs = scenarios[-1]["projected_risk"]
    spread = highs - lows
    held = live_risk - highs
    if score >= 78 and held >= 18 and spread <= 16:
        return "ROBUST"
    if score >= 55 and held >= 8:
        return "MODERATE"
    if score > 0:
        return "FRAGILE"
    return "UNCERTAIN"


def _robustness_score(
    live_risk: float,
    scenarios: list[dict[str, Any]],
    protected: set[str],
    disruption: str,
    pred_conf: float,
    n_alts: int,
    reversible: str,
) -> float:
    if not scenarios:
        return 0.0
    reductions = [max(0.0, live_risk - s["projected_risk"]) for s in scenarios]
    avg_red = sum(reductions) / len(reductions)
    min_red = min(reductions)
    spread = scenarios[-1]["projected_risk"] - scenarios[0]["projected_risk"]
    crit = 10.0 if any(CRIT.get(a) == "CRITICAL" for a in protected) else 3.0
    alt_pen = min(14.0, n_alts * 4.5)
    rev = 6.0 if reversible == "YES" else 0.0
    score = (
        18.0
        + 0.85 * avg_red
        + 0.45 * min_red
        - 0.55 * spread
        + crit
        + rev
        + 0.08 * pred_conf
        - 0.35 * DISRUPT_PENALTY.get(disruption, 16)
        - alt_pen
    )
    return float(max(0, min(100, round(score, 1))))


def _scenarios_for(
    live_risk: float,
    base_risk: float,
    blast_before: int,
    blast_after: int,
    alts: list[str],
    protected: set[str],
    original: str | None,
) -> list[dict[str, Any]]:
    out = []
    gap = max(0.0, live_risk - base_risk)
    primary_alt = alts[0] if alts else None
    for level, score in LEVELS:
        frac = score / 100.0
        alt_used = None
        if not primary_alt:
            outcome = "ATTACK_STALLED"
            residual = base_risk + gap * frac * 0.10
            blast = blast_after
            reason = (
                f"SIMULATION ADAPTATION SCORE {score}: no reachable synthetic alternate remains "
                f"after protecting {', '.join(protected) or 'the selected asset'}."
            )
        elif score <= 30:
            outcome = "ATTACK_STALLED"
            residual = base_risk + gap * 0.06
            blast = blast_after
            reason = "Low simulated adaptation cannot pivot off the blocked primary path."
        elif score <= 50:
            outcome = "RISK_REDUCED"
            residual = base_risk + gap * 0.22
            blast = blast_after
            reason = "Medium simulated adaptation raises residual risk but the primary path stays blocked."
        else:
            outcome = "ALTERNATE_PATH"
            residual = base_risk + gap * frac * 0.58
            alt_used = primary_alt
            blast = min(blast_before, blast_after + (1 if score >= 70 else 0))
            reason = (
                f"The protected asset is unavailable in this simulated branch. "
                f"A graph-reachable alternate {primary_alt} is selected."
            )
        residual = round(min(live_risk, max(base_risk, residual)), 1)
        if primary_alt and score >= 90 and residual >= round(live_risk * 0.97, 1):
            outcome = "DEFENSE_BYPASSED_SIMULATED"
            reason = "Very high simulated adaptation leaves residual risk near the undefended state."
        out.append(
            {
                "adaptation_level": level,
                "adaptation_score": score,
                "projected_risk": residual,
                "blast_radius": int(blast),
                "alternate_target": alt_used,
                "outcome": outcome,
                "reason": reason,
                "simulated": True,
                "label": "SIMULATION ADAPTATION SCORE",
            }
        )
    return out


def _analyze_action(src: dict[str, Any], action: str, forks_by_action: dict[str, Any]) -> dict[str, Any]:
    graph = src.get("attack_graph") or {}
    pred = src.get("prediction") or {}
    detection = src.get("detection") or {}
    original = pred.get("predicted_target")
    live_risk = float(src.get("risk_score") or detection.get("risk_score") or 0)
    applied = apply(action, graph)
    protected = set(applied.get("protected_assets") or [])
    catalog = {o["action"]: o for o in ADAPTIVE_OPTIONS}
    spec = catalog.get(action, {})
    fork = forks_by_action.get(action) or {}
    base_risk = float(fork.get("projected_risk") or max(8.0, live_risk - 20))
    blast_before = int(fork.get("blast_radius_before") or 0)
    blast_after = int(fork.get("blast_radius_after") or blast_before)
    alts = _reachable_alternates(graph.get("current_node"), protected, graph)
    scenarios = _scenarios_for(live_risk, base_risk, blast_before, blast_after, alts, protected, original)
    disruption = spec.get("disruption") or fork.get("operational_disruption") or "MEDIUM"
    reversible = spec.get("reversible") or fork.get("reversibility") or "YES"
    score = _robustness_score(
        live_risk,
        scenarios,
        protected,
        disruption,
        float(pred.get("confidence") or 0),
        len(alts),
        reversible,
    )
    klass = _classify(score, scenarios, live_risk)
    protected_target = next(iter(protected), None)
    return {
        "defense_action": action,
        "title": spec.get("title") or fork.get("title") or action,
        "original_target": original,
        "protected_target": protected_target,
        "robustness_score": score,
        "robustness_class": klass,
        "scenarios": scenarios,
        "alternate_targets": alts,
        "summary": (
            f"{action} is {klass} under simulated attacker adaptation "
            f"(robustness {score}/100). Original target {original or 'none'}; "
            f"protected {protected_target or 'none'}."
        ),
        "simulated": True,
        "label": "SIMULATED adaptation — not a real attacker",
    }


def analyze(state: dict[str, Any] | None) -> dict[str, Any]:
    """Read-only adaptation + robustness from a copy of live state."""
    src = copy.deepcopy(state or {})
    events = src.get("events") or []
    if not events:
        return dict(EMPTY_ADAPTATION)
    forks_payload = src.get("attack_forks") or fork_engine.build(src)
    forks_by_action = {f["defense_action"]: f for f in forks_payload.get("forks") or []}
    options = list((src.get("defense") or {}).get("options") or [])
    if not options:
        options = [{"action": o["action"]} for o in ADAPTIVE_OPTIONS]
    recommended = (src.get("defense") or {}).get("recommended_action") or (options[0]["action"] if options else None)
    comparisons = []
    by_action = {}
    for opt in options:
        action = opt.get("action")
        row = _analyze_action(src, action, forks_by_action)
        by_action[action] = row
        comparisons.append(
            {
                "defense_action": action,
                "title": row["title"],
                "robustness_score": row["robustness_score"],
                "robustness_class": row["robustness_class"],
            }
        )
    primary = by_action.get(recommended) or next(iter(by_action.values()), dict(EMPTY_ADAPTATION))
    primary = dict(primary)
    primary["comparisons"] = comparisons
    primary["fork_best"] = (forks_payload.get("best_fork") or {}).get("defense_action")
    return primary
